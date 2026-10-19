"""Next-candle forecast: LONG or SHORT for the candle starting now, with a % chance and a strength label.

How it works (all on this coin's own recent candles, ~1000 of them):
1. Candlestick patterns are detected (engulfing, hammer, shooting star, doji, three soldiers/crows,
   20-candle breakouts) and the agents' signals are turned into features
   (trend, momentum, price action, volume, taker flow, higher-timeframe trend).
2. Pattern matching: the past moments whose recent candles looked most like now are found,
   and we count how often the next candle went up.
3. A logistic regression learns how the features related to the next candle's direction.
4. The two estimates are blended into one probability.
5. Walk-forward check: the same method is trained on older candles and scored on newer ones it never saw.
   That decides the strength label, so STRONG means "this has actually worked recently", not a guess.
6. Live order flow and the Chief Strategist can downgrade a call they strongly disagree with.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .data import TF_SECONDS, MarketSnapshot
from .indicators import adx, atr, bollinger, ema, macd, rsi, stoch_rsi, vwap
from .odds import wilson

CALL_THRESHOLD = 0.55  # blended probability needed for a MODERATE call
STRONG_THRESHOLD = 0.58
MIN_TEST_CALLS = 30
TAKER_FEE_PCT = 0.04  # per side, typical futures taker fee
NEIGHBOURS = 40
SHAPE_LEN = 8
MAX_HISTORY = 1200  # candles used for training / pattern matching

FEATURE_NAMES = {
    "body": "last candle body", "ret3": "3-candle momentum", "ret10": "10-candle momentum",
    "rsi14": "RSI 14", "rsi7": "RSI 7", "macd": "MACD histogram", "stoch": "Stoch RSI",
    "ema_dist": "distance from EMA 20", "ema_slope": "EMA 20 slope", "bb": "Bollinger position",
    "vwap_dist": "distance from VWAP", "vol": "volume vs average", "upper_wick": "upper-wick rejection",
    "lower_wick": "lower-wick rejection", "adx_dir": "trend strength & direction",
    "taker1": "taker buying (last candle)", "taker3": "taker buying (3 candles)",
    "htf_trend": "higher-timeframe trend", "htf_rsi": "higher-timeframe RSI",
    "pattern": "candlestick patterns", "breakout": "20-candle breakout",
}

BULLISH = {"bullish_engulfing": "Bullish engulfing", "hammer": "Hammer", "three_white_soldiers": "Three white soldiers",
           "breakout_up": "Breakout above 20-candle high"}
BEARISH = {"bearish_engulfing": "Bearish engulfing", "shooting_star": "Shooting star", "three_black_crows": "Three black crows",
           "breakout_down": "Breakdown below 20-candle low"}
NEUTRAL = {"doji": "Doji (indecision)", "inside_bar": "Inside bar (compression)"}


def detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Boolean candlestick-pattern flags for every candle (uses only that candle and earlier ones)."""
    o, h, lo, c = df["open"], df["high"], df["low"], df["close"]
    body = (c - o).abs()
    rng = (h - lo).replace(0, np.nan)
    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - lo
    green, red = c > o, c < o
    po, pc = o.shift(), c.shift()
    p = pd.DataFrame(index=df.index)
    p["bullish_engulfing"] = green & (pc < po) & (c >= po) & (o <= pc) & (body > (pc - po).abs())
    p["bearish_engulfing"] = red & (pc > po) & (c <= po) & (o >= pc) & (body > (pc - po).abs())
    p["hammer"] = (lower >= 2 * body) & (upper <= body) & (body / rng > 0.05)
    p["shooting_star"] = (upper >= 2 * body) & (lower <= body) & (body / rng > 0.05)
    p["doji"] = body / rng <= 0.1
    p["three_white_soldiers"] = green & green.shift(1, fill_value=False) & green.shift(2, fill_value=False) \
        & (c > c.shift()) & (c.shift() > c.shift(2))
    p["three_black_crows"] = red & red.shift(1, fill_value=False) & red.shift(2, fill_value=False) \
        & (c < c.shift()) & (c.shift() < c.shift(2))
    p["inside_bar"] = (h < h.shift()) & (lo > lo.shift())
    p["breakout_up"] = c > h.shift().rolling(20).max()
    p["breakout_down"] = c < lo.shift().rolling(20).min()
    return p.fillna(False).astype(bool)


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
    pats = detect_patterns(df)
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
    f["vol"] = np.log(df["volume"].replace(0, np.nan) / df["volume"].rolling(20).mean().replace(0, np.nan))
    f["upper_wick"] = (h - np.maximum(o, c)) / rng
    f["lower_wick"] = (np.minimum(o, c) - lo) / rng
    f["adx_dir"] = adx_v / 50 * np.sign(pdi - mdi)
    f["pattern"] = (pats[["bullish_engulfing", "hammer", "three_white_soldiers"]].sum(axis=1)
                    - pats[["bearish_engulfing", "shooting_star", "three_black_crows"]].sum(axis=1)).astype(float)
    f["breakout"] = pats["breakout_up"].astype(float) - pats["breakout_down"].astype(float)
    if "taker_buy_volume" in df.columns and df["taker_buy_volume"].gt(0).any():
        vol = df["volume"].replace(0, np.nan)
        f["taker1"] = df["taker_buy_volume"] / vol - 0.5
        f["taker3"] = df["taker_buy_volume"].rolling(3).sum() / df["volume"].rolling(3).sum().replace(0, np.nan) - 0.5

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


def candle_shapes(df: pd.DataFrame) -> pd.DataFrame:
    """The shape of the last SHAPE_LEN candles (bodies and wicks in ATR units) — used for pattern matching."""
    a = atr(df).replace(0, np.nan)
    body = (df["close"] - df["open"]) / a
    upper = (df["high"] - df[["open", "close"]].max(axis=1)) / a
    lower = (df[["open", "close"]].min(axis=1) - df["low"]) / a
    cols = {}
    for k in range(SHAPE_LEN):
        w = 1 / (1 + k)  # the most recent candles matter most when matching shapes
        cols[f"b{k}"] = body.shift(k) * w
        if k < 2:
            cols[f"u{k}"] = upper.shift(k) * w * 0.5
            cols[f"l{k}"] = lower.shift(k) * w * 0.5
    cols["trend"] = (df["close"] - df["close"].shift(SHAPE_LEN)) / a * 0.3
    return pd.DataFrame(cols, index=df.index).clip(-5, 5)


def _fit_logistic(X: np.ndarray, y: np.ndarray, l2: float = 50.0, iters: int = 25) -> np.ndarray:
    """Ridge-regularised logistic regression via Newton steps. X already includes a bias column.

    Up and down candles get equal total weight, so the model can't just learn "down was more common
    lately" and say SHORT every time — the direction has to come from the signals.
    """
    up = y.mean() if len(y) else 0.5
    sw = np.where(y == 1, 0.5 / max(up, 1e-6), 0.5 / max(1 - up, 1e-6))
    w = np.zeros(X.shape[1])
    reg = np.full(X.shape[1], l2)
    reg[0] = 0  # don't shrink the intercept
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ w, -30, 30)))
        grad = X.T @ (sw * (p - y)) + reg * w
        hess = (X * (sw * p * (1 - p))[:, None]).T @ X + np.diag(reg) + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(hess, grad)
        w -= step
        if np.abs(step).max() < 1e-6:
            break
    return w


class _Model:
    """Blend of a logistic regression on the agents' features and nearest-neighbour pattern matching."""

    def __init__(self, X: pd.DataFrame, S: pd.DataFrame, y: np.ndarray):
        self.cols = list(X.columns)
        self.mu = X.mean().values
        self.sd = X.std().replace(0, 1).fillna(1).values
        self.w = _fit_logistic(self._design(X), y)
        self.S, self.y = S.values, y
        self.s_sd = float(np.nanmean(S.std().values)) or 1.0
        self.weights = (0.5, 0.5)

    def _design(self, X: pd.DataFrame) -> np.ndarray:
        Z = (X[self.cols].values - self.mu) / self.sd
        return np.column_stack([np.ones(len(Z)), Z])

    def predict_model(self, X: pd.DataFrame) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(self._design(X) @ self.w, -30, 30)))

    def predict_patterns(self, S: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Share of the NEIGHBOURS most similar past setups whose next candle went up (shrunk toward 50%)."""
        q = S.values / self.s_sd
        ref = self.S / self.s_sd
        d = ((q[:, None, :] - ref[None, :, :]) ** 2).sum(axis=2)
        k = min(NEIGHBOURS, len(ref))
        idx = np.argpartition(d, k - 1, axis=1)[:, :k]
        ups = self.y[idx].sum(axis=1)
        # Compare with how common up-candles were overall, so a downtrend alone doesn't mean SHORT.
        prior = min(max(self.y.mean(), 0.05), 0.95)
        rate_up = (ups + 2.5 * prior) / (k + 2.5)
        odds = (rate_up / (1 - rate_up)) / (prior / (1 - prior))
        p = odds / (1 + odds)
        return 0.5 + (p - 0.5) * k / (k + 5), ups

    def predict(self, X: pd.DataFrame, S: pd.DataFrame) -> np.ndarray:
        wm, wp = self.weights
        return wm * self.predict_model(X) + wp * self.predict_patterns(S)[0]

    def drivers(self, x: pd.DataFrame, n: int = 4) -> list[tuple[str, float]]:
        contrib = ((x[self.cols].values[0] - self.mu) / self.sd) * self.w[1:]
        order = np.argsort(-np.abs(contrib))[:n]
        return [(self.cols[i], float(contrib[i])) for i in order]


def _fit(F: pd.DataFrame, S: pd.DataFrame, y: np.ndarray) -> _Model:
    """Fit both methods; weight them by how well each predicted the last 20% of the training window."""
    k = int(len(F) * 0.8)
    weights = (0.5, 0.5)
    if k >= 100 and len(F) - k >= 30:
        probe = _Model(F.iloc[:k], S.iloc[:k], y[:k])
        acc_m = ((probe.predict_model(F.iloc[k:]) >= 0.5) == (y[k:] == 1)).mean()
        acc_p = ((probe.predict_patterns(S.iloc[k:])[0] >= 0.5) == (y[k:] == 1)).mean()
        sm, sp = max(acc_m - 0.5, 0.01), max(acc_p - 0.5, 0.01)
        weights = (sm / (sm + sp), sp / (sm + sp))
    model = _Model(F, S, y)
    model.weights = weights
    return model


def _walk_forward(F: pd.DataFrame, S: pd.DataFrame, y: np.ndarray) -> dict:
    """Train on the past, test on the following unseen block; repeat 3 times and pool the results."""
    n = len(F)
    probs, actual = [], []
    for start in (0.55, 0.70, 0.85):
        a, b = int(n * start), min(int(n * (start + 0.15)), n)
        if a < 100 or b <= a:
            continue
        m = _fit(F.iloc[:a], S.iloc[:a], y[:a])
        probs.append(m.predict(F.iloc[a:b], S.iloc[a:b]))
        actual.append(y[a:b])
    if not probs:
        return {"tested": 0, "calls": 0, "call_accuracy": None, "call_accuracy_95ci": None}
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
    S_all = candle_shapes(closed)
    nxt = closed["close"].shift(-1)
    y_all = (nxt > closed["close"]).astype(float).values
    moved = (nxt != closed["close"]).to_numpy()  # flat candles are neither up nor down: don't learn from them
    valid = (F_all.notna().all(axis=1) & S_all.notna().all(axis=1)).to_numpy() & moved
    valid[-1] = False  # the last closed candle's "next" candle is the one we're predicting
    F, S, y = F_all[valid], S_all[valid], y_all[valid]
    F, S, y = F.tail(MAX_HISTORY), S.tail(MAX_HISTORY), y[-MAX_HISTORY:]  # bounded memory & time
    if len(F) < 200:
        return {"error": f"Not enough {tf} history to forecast ({len(F)} usable candles, need 200). "
                         f"Try a shorter timeframe or a coin with more trading history."}

    test = _walk_forward(F, S, y)
    model = _fit(F, S, y)
    x_now = F_all.iloc[[-1]].fillna(0)
    s_now = S_all.iloc[[-1]].fillna(0)
    p_model = float(model.predict_model(x_now)[0])
    p_pat_arr, ups = model.predict_patterns(s_now)
    p_pattern = float(p_pat_arr[0])
    wm, wp = model.weights
    p_up = wm * p_model + wp * p_pattern

    direction = "LONG" if p_up >= 0.5 else "SHORT"
    sign = 1 if direction == "LONG" else -1
    chance = p_up if direction == "LONG" else 1 - p_up
    edge = (test.get("calls", 0) >= MIN_TEST_CALLS and test["call_accuracy"] is not None
            and test["call_accuracy_95ci"][0] > 0.5 and test["call_accuracy"] > test["majority_baseline"])
    agree = (p_model - 0.5) * (p_pattern - 0.5) > 0

    # ---- plain-English reasons
    why = []
    last = detect_patterns(closed).iloc[-1]
    seen = [(name, +1) for key, name in BULLISH.items() if last[key]] + \
           [(name, -1) for key, name in BEARISH.items() if last[key]] + \
           [(name, 0) for key, name in NEUTRAL.items() if last[key]]
    patterns = [{"name": n, "bias": "UP" if b > 0 else "DOWN" if b < 0 else "NEUTRAL"} for n, b in seen]
    if seen:
        why.append("Candle pattern on the last closed candle: " + ", ".join(n for n, _ in seen))
    k = min(NEIGHBOURS, len(S))
    why.append(f"Pattern match: in the {k} most similar past setups on this coin, the next candle went up "
               f"{int(ups[0])} times and down {k - int(ups[0])} times → {p_pattern:.0%} up")
    drivers = [{"feature": FEATURE_NAMES.get(n, n), "push": "UP" if v > 0 else "DOWN", "weight": abs(v)}
               for n, v in model.drivers(x_now, n=5)]
    ups_d = [d["feature"] for d in drivers if d["push"] == "UP"]
    downs_d = [d["feature"] for d in drivers if d["push"] == "DOWN"]
    why.append(f"Indicator model: {p_model:.0%} up"
               + (f" — pushing up: {', '.join(ups_d)}" if ups_d else "")
               + (f"; pushing down: {', '.join(downs_d)}" if downs_d else ""))

    # ---- strength
    warnings = []
    if decision is not None:
        of = next((r for r in decision.reports if r.agent == "Order Flow Analyst"), None)
        if of and of.confidence > 0:
            if of.score * sign < -0.4:
                warnings.append(f"Live order flow disagrees: {of.summary.lower()}")
            elif of.score * sign > 0.15:
                why.append(f"Live order flow agrees: {of.summary.lower()}")
        if decision.action in ("LONG", "SHORT") and decision.action != direction and decision.setup_quality >= 50:
            warnings.append(f"The bigger picture (Chief Strategist) favours {decision.action}")
    if agree:
        why.append(f"Both methods point {'UP' if p_up >= 0.5 else 'DOWN'}")
    if chance >= STRONG_THRESHOLD and edge and agree and not warnings:
        strength, advice = "STRONG", "Good setup: this method has beaten chance on recent unseen candles"
    elif chance >= CALL_THRESHOLD and edge and not warnings:
        strength, advice = "MODERATE", "Possible trade: use a small size"
    else:
        strength, advice = "WEAK", "Better to skip this candle: the odds are close to a coin flip"
        if not edge:
            warnings.append("Recent accuracy on unseen candles isn't clearly better than chance")
        elif chance < CALL_THRESHOLD:
            warnings.append(f"The chance is below {CALL_THRESHOLD:.0%}")

    if forming and elapsed > 0.3 * step:
        warnings.append(f"This candle is already {elapsed / step:.0%} done — entering late reduces the edge")
    move_pct = float(((closed["close"] - closed["open"]).abs() / closed["open"]).tail(200).median() * 100)
    fee_round_trip = 2 * TAKER_FEE_PCT
    if move_pct < 2 * fee_round_trip:
        warnings.append(f"A typical {tf} candle moves only {move_pct:.3f}% and fees cost about "
                        f"{fee_round_trip:.2f}% per trade — consider a higher timeframe")

    price = float(df["close"].iloc[-1])
    a = float(atr(closed).iloc[-1])
    plan = {"entry": price, "stop_loss": price - sign * a, "take_profit": price + sign * a,
            "exit": f"if neither level is hit, close the trade when this {tf} candle closes"}

    return {
        "symbol": snap.symbol, "timeframe": tf,
        "direction": direction, "chance": chance, "strength": strength, "advice": advice,
        "action": direction if strength != "WEAK" else "NO TRADE",
        "probability_up": p_up, "probability_down": 1 - p_up,
        "pattern_match_up": p_pattern, "model_up": p_model, "methods_agree": bool(agree),
        "method_weights": {"indicators": wm, "pattern_match": wp},
        "patterns": patterns, "why": why, "warnings": warnings, "drivers": drivers, "plan": plan,
        "target_candle_open": target_open, "target_candle_close": target_open + step,
        "seconds_elapsed": elapsed if forming else 0.0, "price": price,
        "model_test": test, "has_edge": bool(edge),
        "typical_move_pct": move_pct, "fees_round_trip_pct": fee_round_trip,
        "trained_on": int(len(F)), "data_notes": list(snap.notes),
        "recent_up_rate": float(y[-200:].mean()), "flat_candle_rate": float(1 - moved[:-1].mean()),
        "note": "The % is learned from this coin's recent candles, not guessed. One-candle moves are "
                "close to random, so 55-60% is a good reading. No prediction is ever certain.",
    }
