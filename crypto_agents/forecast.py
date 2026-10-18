"""Next-candle forecast: LONG / SHORT / NO TRADE for the candle that is starting now, with a probability.

How it works
1. The agents' signals (trend, momentum, price action, volume, taker flow, higher-timeframe trend) are
   turned into features for every closed candle of this coin and timeframe (~1000 candles).
2. A logistic regression learns how those features related to the NEXT candle closing up or down.
3. Walk-forward test: the model is trained on older candles and scored on newer candles it never saw.
   Only if it beat a coin-flip/majority guess there do we allow a LONG/SHORT call.
4. Live order flow and the Chief Strategist can veto a call they strongly disagree with.

The probability is learned from data, not invented; one-candle moves are mostly noise, so expect
numbers like 52-60%, not 90%+.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .data import TF_SECONDS, MarketSnapshot
from .indicators import adx, atr, bollinger, ema, macd, rsi, stoch_rsi, vwap
from .odds import wilson

CALL_THRESHOLD = 0.55  # model probability needed to call LONG (or <= 0.45 for SHORT)
MIN_TEST_CALLS = 30
TAKER_FEE_PCT = 0.04  # per side, typical futures taker fee

FEATURE_NAMES = {
    "body": "last candle body", "ret3": "3-candle momentum", "ret10": "10-candle momentum",
    "rsi14": "RSI 14", "rsi7": "RSI 7", "macd": "MACD histogram", "stoch": "Stoch RSI",
    "ema_dist": "distance from EMA 20", "ema_slope": "EMA 20 slope", "bb": "Bollinger position",
    "vwap_dist": "distance from VWAP", "vol": "volume vs average", "upper_wick": "upper-wick rejection",
    "lower_wick": "lower-wick rejection", "adx_dir": "trend strength & direction",
    "taker1": "taker buying (last candle)", "taker3": "taker buying (3 candles)",
    "htf_trend": "higher-timeframe trend", "htf_rsi": "higher-timeframe RSI",
}


def build_features(snap: MarketSnapshot, df: pd.DataFrame) -> pd.DataFrame:
    """One row per candle of `df`, using only information available when that candle closed."""
    c, o, h, lo = df["close"], df["open"], df["high"], df["low"]
    a = atr(df).replace(0, np.nan)
    rng = (h - lo).replace(0, np.nan)
    e20 = ema(c, 20)
    _, _, hist = macd(c)
    k, _ = stoch_rsi(c)
    bl, bm, bu = bollinger(c)
    adx_v, pdi, mdi = adx(df)
    f = pd.DataFrame(index=df.index)
    f["body"] = (c - o) / a
    f["ret3"] = (c - c.shift(3)) / a
    f["ret10"] = (c - c.shift(10)) / a
    f["rsi14"] = (rsi(c) - 50) / 50
    f["rsi7"] = (rsi(c, 7) - 50) / 50
    f["macd"] = hist / a
    f["stoch"] = (k - 50) / 50
    f["ema_dist"] = (c - e20) / a
    f["ema_slope"] = (e20 - e20.shift(3)) / a
    f["bb"] = ((c - bm) / ((bu - bl) / 2).replace(0, np.nan))
    f["vwap_dist"] = (c - vwap(df)) / a
    f["vol"] = np.log(df["volume"] / df["volume"].rolling(20).mean())
    f["upper_wick"] = (h - np.maximum(o, c)) / rng
    f["lower_wick"] = (np.minimum(o, c) - lo) / rng
    f["adx_dir"] = adx_v / 50 * np.sign(pdi - mdi)
    if "taker_buy_volume" in df.columns:
        vol = df["volume"].replace(0, np.nan)
        f["taker1"] = df["taker_buy_volume"] / vol - 0.5
        f["taker3"] = df["taker_buy_volume"].rolling(3).sum() / df["volume"].rolling(3).sum() - 0.5

    # Higher-timeframe context, aligned so each row only sees higher candles that had already closed.
    tfs = list(snap.candles)
    entry_tf = snap.entry_timeframe
    if len(tfs) >= 2:
        htf = tfs[-2]
        hdf = snap.candles[htf]
        hc = hdf["close"]
        ctx = pd.DataFrame({
            "htf_trend": ((hc - ema(hc, 20)) / atr(hdf).replace(0, np.nan)).values,
            "htf_rsi": ((rsi(hc) - 50) / 50).values,
            "t": hdf.index + pd.Timedelta(seconds=TF_SECONDS[htf]),
        })
        rows = pd.DataFrame({"t": df.index + pd.Timedelta(seconds=TF_SECONDS[entry_tf])})
        merged = pd.merge_asof(rows, ctx.sort_values("t"), on="t", direction="backward")
        f["htf_trend"] = merged["htf_trend"].values
        f["htf_rsi"] = merged["htf_rsi"].values
    return f.replace([np.inf, -np.inf], np.nan).clip(-5, 5)


def _fit_logistic(X: np.ndarray, y: np.ndarray, l2: float = 50.0, iters: int = 25) -> np.ndarray:
    """Ridge-regularised logistic regression via Newton steps. X already includes a bias column."""
    w = np.zeros(X.shape[1])
    reg = np.full(X.shape[1], l2)
    reg[0] = 0  # don't shrink the intercept
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        grad = X.T @ (p - y) + reg * w
        hess = (X * (p * (1 - p))[:, None]).T @ X + np.diag(reg) + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(hess, grad)
        w -= step
        if np.abs(step).max() < 1e-6:
            break
    return w


class _Model:
    def __init__(self, X: pd.DataFrame, y: np.ndarray):
        self.cols = list(X.columns)
        self.mu = X.mean().values
        self.sd = X.std().replace(0, 1).fillna(1).values
        self.w = _fit_logistic(self._design(X), y)

    def _design(self, X: pd.DataFrame) -> np.ndarray:
        Z = (X[self.cols].values - self.mu) / self.sd
        return np.column_stack([np.ones(len(Z)), Z])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(self._design(X) @ self.w, -30, 30)))

    def drivers(self, x: pd.DataFrame, n: int = 4) -> list[tuple[str, float]]:
        contrib = ((x[self.cols].values[0] - self.mu) / self.sd) * self.w[1:]
        order = np.argsort(-np.abs(contrib))[:n]
        return [(self.cols[i], float(contrib[i])) for i in order]


def _walk_forward(F: pd.DataFrame, y: np.ndarray) -> dict:
    """Train on the past, test on the following unseen block; repeat 3 times and pool the results."""
    n = len(F)
    probs, actual = [], []
    for start in (0.55, 0.70, 0.85):
        a, b = int(n * start), min(int(n * (start + 0.15)), n)
        if a < 100 or b <= a:
            continue
        m = _Model(F.iloc[:a], y[:a])
        probs.append(m.predict(F.iloc[a:b]))
        actual.append(y[a:b])
    if not probs:
        return {"tested": 0}
    p, t = np.concatenate(probs), np.concatenate(actual)
    called = (p >= CALL_THRESHOLD) | (p <= 1 - CALL_THRESHOLD)
    correct = ((p >= 0.5) == (t == 1))
    calls = int(called.sum())
    hits = int(correct[called].sum())
    lo, hi = wilson(hits, calls)
    return {
        "tested": len(t),
        "accuracy_all": float(correct.mean()),
        "calls": calls,
        "call_accuracy": hits / calls if calls else None,
        "call_accuracy_95ci": [lo, hi] if calls else None,
        "majority_baseline": float(max(t.mean(), 1 - t.mean())),
        "up_rate": float(t.mean()),
    }


def next_candle(snap: MarketSnapshot, decision=None, now: float | None = None) -> dict:
    now = now or time.time()
    tf = snap.entry_timeframe
    step = TF_SECONDS[tf]
    df = snap.candles[tf]
    last_open = df.index[-1].timestamp()
    forming = last_open + step > now
    closed = df.iloc[:-1] if forming else df
    target_open = last_open if forming else last_open + step
    elapsed = max(0.0, now - target_open)

    F_all = build_features(snap, closed)
    y_all = (closed["close"].shift(-1) > closed["close"]).astype(float).values
    valid = F_all.notna().all(axis=1).to_numpy().copy()
    valid[-1] = False  # the last closed candle's "next" candle is the one we're predicting
    F, y = F_all[valid], y_all[valid]
    if len(F) < 200:
        return {"error": f"Not enough history on {tf} to train a forecast ({len(F)} usable candles)"}

    test = _walk_forward(F, y)
    model = _Model(F, y)
    x_now = F_all.iloc[[-1]].fillna(0)
    p_up = float(model.predict(x_now)[0])

    move_pct = float(((closed["close"] - closed["open"]).abs() / closed["open"]).tail(200).median() * 100)
    fee_round_trip = 2 * TAKER_FEE_PCT

    reasons, vetoes = [], []
    # Edge = accuracy on unseen candles is statistically above 50% AND above always guessing the majority.
    edge = (test.get("calls", 0) >= MIN_TEST_CALLS and test["call_accuracy"] is not None
            and test["call_accuracy_95ci"][0] > 0.5 and test["call_accuracy"] > test["majority_baseline"])
    direction = "LONG" if p_up >= CALL_THRESHOLD else "SHORT" if p_up <= 1 - CALL_THRESHOLD else None
    action = direction or "NO TRADE"

    if direction is None:
        reasons.append(f"Probability {p_up:.0%} up / {1 - p_up:.0%} down is too close to 50/50 "
                       f"(needs ≥{CALL_THRESHOLD:.0%} either way)")
    if direction and not edge:
        vetoes.append("The model did not beat a simple guess on recent unseen candles of this coin "
                      "— no proven edge right now")
    if direction and decision is not None:
        of = next((r for r in decision.reports if r.agent == "Order Flow Analyst"), None)
        sign = 1 if direction == "LONG" else -1
        if of and of.confidence > 0 and of.score * sign < -0.4:
            vetoes.append(f"Live order flow strongly disagrees ({of.summary.lower()})")
        if decision.action in ("LONG", "SHORT") and decision.action != direction and decision.setup_quality >= 50:
            vetoes.append(f"Chief Strategist has a strong {decision.action} setup on the bigger picture")
    if vetoes:
        action = "NO TRADE"
    if forming and elapsed > 0.3 * step:
        reasons.append(f"Late entry: this candle is already {elapsed / step:.0%} done — "
                       f"better to wait for the next forecast at candle close")
    if move_pct < 2 * fee_round_trip:
        reasons.append(f"Typical {tf} candle moves only {move_pct:.3f}%, while fees are about "
                       f"{fee_round_trip:.2f}% per round trip — fees eat most one-candle profits")

    drivers = [{"feature": FEATURE_NAMES.get(n, n), "push": "UP" if v > 0 else "DOWN", "weight": abs(v)}
               for n, v in model.drivers(x_now)]
    price = float(df["close"].iloc[-1])
    a = float(atr(closed).iloc[-1])
    plan = None
    if action != "NO TRADE":
        sign = 1 if action == "LONG" else -1
        plan = {"entry": price, "stop_loss": price - sign * a, "take_profit": price + sign * a,
                "exit": f"close the trade when this {tf} candle closes if neither level is hit"}

    return {
        "symbol": snap.symbol, "timeframe": tf, "action": action,
        "probability_up": p_up, "probability_down": 1 - p_up,
        "target_candle_open": target_open, "target_candle_close": target_open + step,
        "seconds_elapsed": elapsed if forming else 0.0, "price": price,
        "reasons": reasons, "vetoes": vetoes, "drivers": drivers, "plan": plan,
        "model_test": test, "has_edge": bool(edge),
        "typical_move_pct": move_pct, "fees_round_trip_pct": fee_round_trip,
        "trained_on": int(len(F)),
        "note": "Probability learned from this coin's recent candles and checked on unseen candles. "
                "One-candle direction is close to random; never risk much on a single candle.",
    }
