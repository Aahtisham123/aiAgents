"""Pro trade plan: what a professional trader checks before a trade, then exactly where to enter.

The workflow is ported from three open-source Claude skill packs and adapted to 24/7 crypto, long or short:

- day-trader-skill (github.com/Jakeschincariol/day-trader-skill):
  scanner setups -> entry timer -> exit planner -> Time Machine -> budget -> risk manager.
  The entry only counts on a CLOSED candle beyond the level (a wick is not an entry). The stop and the
  target are set before the entry. The Time Machine replays the plan 10,000 times from the coin's own
  candles and re-runs the same rule on past data, then gives one honest verdict against break-even.
- trader-skill (github.com/Jakeschincariol/trader-skill): the original budget sizing and risk limits.
- claude-trading-skills (github.com/tradermonty/claude-trading-skills): crypto-regime-analyzer
  (0-100 regime score), drawdown-circuit-breaker, pre-trade-discipline-gate, breakout-trade-planner
  (max 8% risk, don't chase), position-sizer.

Nothing here places an order. A GO is a rules check, not a promise that the trade wins.
"""
from __future__ import annotations

import math
import time

import numpy as np
import pandas as pd

from .data import TF_SECONDS, MarketSnapshot
from .indicators import atr, ema, rsi, sma
from .strategist import HORIZON

FEE = 0.0004  # taker fee per side
SEED = 19  # same seed as the Time Machine, so every run can be repeated
REPLAYS = 10_000
OR_BARS = {"1m": 15, "5m": 3, "15m": 4}  # opening range of the UTC day: 15 min, 15 min, 1 hour
LEVEL_LOOKBACK = 20
STOP_ATR = 1.5
CHASE_R = 0.5  # more than half the risk past the trigger is a late entry
MAX_RISK_PCT = 8.0  # breakout-trade-planner: a stop wider than 8% is not a plan
MIN_RISK_PCT = 0.05  # trader-exit: a stop tighter than this can't survive the spread
COIN_FLIP, STRONG, MANY_NEITHER = 0.05, 0.15, 0.40  # Time Machine verdict thresholds
INTRADAY = ("1m", "5m", "15m")

# Account-protection rules. Intraday trades come faster, so the cool-downs are shorter.
RULES = {
    "intraday": {"revenge_minutes": 30, "losing_streak": 3, "cooldown_hours": 2, "max_trades_per_day": 6},
    "swing": {"revenge_minutes": 24 * 60, "losing_streak": 2, "cooldown_hours": 24, "max_trades_per_day": 3},
}
DAILY_LOSS_PCT, WEEKLY_LOSS_PCT, MONTHLY_LOSS_PCT = 2.0, 5.0, 8.0  # drawdown-circuit-breaker defaults


def _sign(side: str) -> int:
    return 1 if side == "LONG" else -1


def _decimals(price: float) -> int:
    return max(2, min(10, 5 - int(math.floor(math.log10(abs(price))))) if price else 2)


def _round(x: float, price: float, away_from: float | None = None) -> float:
    """Round to a sensible tick. A stop rounds AWAY from the entry (trader-exit's rule)."""
    d = _decimals(price)
    if away_from is None:
        return round(x, d)
    f = 10 ** d
    return math.floor(x * f) / f if x < away_from else math.ceil(x * f) / f


def _closed(df: pd.DataFrame, tf: str, now: float) -> pd.DataFrame:
    """Only finished candles count. The last row from Binance is the live one while it is still forming."""
    if len(df) and df.index[-1].timestamp() + TF_SECONDS[tf] > now:
        return df.iloc[:-1]
    return df


def _fmt(x: float) -> str:
    return f"{x:,.2f}" if abs(x) >= 1 else f"{x:.6g}"


def _step(key, title, skill, status, summary, details=None, data=None) -> dict:
    return {"key": key, "title": title, "skill": skill, "status": status, "summary": summary,
            "details": details or [], "data": data or {}}


# ================================================================ 1. market regime (crypto-regime-analyzer)

def _trend_structure(close: pd.Series) -> tuple[float, str] | None:
    """BTC Trend Structure table from the regime methodology: price vs the 50/200-day stack + 200-day slope."""
    if len(close) < 220:
        return None
    p, m50, m200 = float(close.iloc[-1]), float(sma(close, 50).iloc[-1]), float(sma(close, 200).iloc[-1])
    slope = (m200 / float(sma(close, 200).iloc[-21]) - 1) * 100
    if p > m50 > m200:
        base, txt = 90, "bull stack (price > 50-day > 200-day)"
    elif m50 > m200 and m200 <= p <= m50:
        base, txt = 65, "pullback inside an intact uptrend"
    elif m50 > m200 and p < m200:
        base, txt = 55, "below both averages, 50-day still above 200-day"
    elif p > m50 and m50 <= m200:
        base, txt = 45, "recovery attempt (price > 50-day, 50-day below 200-day)"
    elif p < m50 < m200:
        base, txt = 15, "bear stack (price < 50-day < 200-day)"
    else:
        base, txt = 50, "flat / mixed"
    mod = 10 if slope > 0.5 else -10 if slope < -0.5 else 0
    txt += f"; 200-day {'rising' if mod > 0 else 'falling' if mod < 0 else 'flat'} ({slope:+.1f}% in 20 days)"
    if abs(m50 / m200 - 1) < 0.015:
        txt += "; 50/200 cross is close"
    return float(min(100, max(0, base + mod))), txt


def _funding_score(rate: float) -> tuple[float, str]:
    pct = rate * 100
    for hi, score, txt in ((-0.010, 80, "washed out, shorts are paying"), (0.0, 65, "skeptical"),
                           (0.010, 75, "neutral"), (0.030, 55, "long leverage building"),
                           (0.060, 30, "crowded longs")):
        if pct <= hi:
            return score, f"funding {pct:+.4f}% per 8h: {txt}"
    return 10, f"funding {pct:+.4f}% per 8h: euphoric, liquidation-cascade risk"


def _drawdown_vol(close: pd.Series) -> tuple[float, str] | None:
    if len(close) < 365:
        return None
    year = close.tail(365)
    dd = (1 - float(close.iloc[-1]) / float(year.max())) * 100
    base = next(s for lim, s in ((10, 90), (20, 75), (35, 55), (50, 35), (65, 20), (1e9, 10)) if dd <= lim)
    logret = np.log(close).diff()
    vol = logret.rolling(30).std() * math.sqrt(365) * 100
    hist = vol.tail(365).iloc[::7].dropna()
    now_vol = float(vol.iloc[-1])
    rank = float((hist < now_vol).mean()) if len(hist) else 0.5
    mod = 10 if rank < 1 / 3 else -10 if rank > 2 / 3 else 0
    score = base + mod
    if dd > 65 and rank > 2 / 3:
        score = max(score, 15)
    return float(min(100, max(0, score))), (f"BTC {dd:.0f}% below its 1-year high, 30-day volatility {now_vol:.0f}% "
                                            f"({'low' if mod > 0 else 'high' if mod < 0 else 'normal'} for the year)")


def market_regime(snap: MarketSnapshot, coin_daily: pd.DataFrame | None, btc_daily: pd.DataFrame | None) -> dict:
    """0-100 regime score (100 = risk-on). Weights from crypto-regime-analyzer; missing parts are redistributed.

    Adapted: the alt-breadth slot is filled by the coin's own daily trend structure, and dominance and
    momentum breadth need a whole-market history this app doesn't download, so they are left out.
    """
    comps = []
    btc = btc_daily if btc_daily is not None else (coin_daily if snap.symbol.startswith("BTC") else None)
    if btc is not None and (r := _trend_structure(btc["close"])):
        comps.append(("BTC trend structure", 25, *r))
    if coin_daily is not None and not snap.symbol.startswith("BTC") and (r := _trend_structure(coin_daily["close"])):
        comps.append((f"{snap.symbol} trend structure", 20, *r))
    if snap.funding_rate is not None:
        comps.append(("Perpetual funding", 15, *_funding_score(snap.funding_rate)))
    if btc is not None and (r := _drawdown_vol(btc["close"])):
        comps.append(("Drawdown & volatility", 15, *r))
    total = sum(w for _, w, _, _ in comps)
    if len(comps) < 2 or total < 40:
        return {"score": None, "zone": "UNKNOWN", "components": [{"name": n, "weight": w, "score": s, "signal": t}
                                                               for n, w, s, t in comps],
                "posture": "Not enough daily history to score the market regime."}
    score = sum(w * s for _, w, s, _ in comps) / total
    zone = "RISK_ON" if score >= 80 else "RISK_OFF" if score < 40 else "NEUTRAL"
    posture = {"RISK_ON": "Broad risk-on conditions: longs have the wind behind them.",
               "NEUTRAL": "Mixed conditions: no strong regime tailwind either way.",
               "RISK_OFF": "Defensive conditions: longs fight the tide, keep size small."}[zone]
    return {"score": round(score, 1), "zone": zone, "posture": posture,
            "components": [{"name": n, "weight": round(w / total * 100), "score": s, "signal": t} for n, w, s, t in comps]}


# ================================================================ 2. setups (trader-scanner)

def scan_setups(df: pd.DataFrame) -> list[dict]:
    """The scanner's rules on this timeframe's closed candles, for both directions."""
    c = df["close"]
    if len(c) < 40:
        return []
    a = float(atr(df).iloc[-1]) or 1e-12
    r = rsi(c)
    m20 = sma(c, 20)
    out = []

    def add(name, bias, detail):
        out.append({"name": name, "bias": bias, "detail": detail})

    prev20 = c.iloc[-21:-1]
    if c.iloc[-1] > prev20.max():
        add("20-candle closing-high breakout", "LONG", f"closed {_fmt(c.iloc[-1])} above every close of the last 20")
    if c.iloc[-1] < prev20.min():
        add("20-candle closing-low breakdown", "SHORT", f"closed {_fmt(c.iloc[-1])} below every close of the last 20")
    impulse = (c.iloc[-6] - c.iloc[-16]) / a
    flag_range = (c.iloc[-5:].max() - c.iloc[-5:].min()) / a
    if impulse > 3 and flag_range < 1.5:
        add("Bull flag", "LONG", f"{impulse:.1f} ATR rally, then 5 candles inside {flag_range:.1f} ATR")
    if impulse < -3 and flag_range < 1.5:
        add("Bear flag", "SHORT", f"{-impulse:.1f} ATR drop, then 5 candles inside {flag_range:.1f} ATR")
    if c.iloc[-2] < m20.iloc[-2] and c.iloc[-1] > m20.iloc[-1]:
        add("Reclaimed the 20 average", "LONG", f"closed back above the 20-candle average {_fmt(m20.iloc[-1])}")
    if c.iloc[-2] > m20.iloc[-2] and c.iloc[-1] < m20.iloc[-1]:
        add("Lost the 20 average", "SHORT", f"closed back below the 20-candle average {_fmt(m20.iloc[-1])}")
    if r.iloc[-1] < 30:
        add("Oversold", "LONG", f"RSI {r.iloc[-1]:.0f}: stretched down, bounces are likely but not a trigger")
    elif r.iloc[-2] < 30 and c.iloc[-1] > c.iloc[-2]:
        add("Oversold bounce", "LONG", "RSI was under 30 and the last candle closed up")
    if r.iloc[-1] > 70:
        add("Overbought", "SHORT", f"RSI {r.iloc[-1]:.0f}: stretched up, pullbacks are likely but not a trigger")
    elif r.iloc[-2] > 70 and c.iloc[-1] < c.iloc[-2]:
        add("Overbought fade", "SHORT", "RSI was over 70 and the last candle closed down")
    return out


# ================================================================ 3. entry timer (trader-entry)

def _opening_range(df: pd.DataFrame, tf: str, day: pd.Timestamp) -> dict | None:
    n = OR_BARS.get(tf)
    if not n:
        return None
    step = pd.Timedelta(seconds=TF_SECONDS[tf])
    bars = df[(df.index >= day) & (df.index < day + n * step)]
    if len(bars) < n:
        return {"day": day, "complete": False, "bars": len(bars), "needed": n}
    return {"day": day, "complete": True, "high": float(bars["high"].max()), "low": float(bars["low"].min()),
            "end": day + n * step, "bars": n, "needed": n}


def _stop(df_atr: np.ndarray, lows: np.ndarray, highs: np.ndarray, i: int, side: str, entry: float,
          setup: str, orr: dict | None) -> tuple[float, str]:
    """Where the setup has failed. ORB: the range midpoint (trader-exit's default). Level: behind the last
    10 candles' extreme, kept between 1 and 3 ATR from the entry, else 1.5 ATR."""
    a = float(df_atr[i])
    s = _sign(side)
    if setup == "orb" and orr:
        mid = (orr["high"] + orr["low"]) / 2
        if (entry - mid) * s > 0:
            return mid, f"opening-range midpoint ({_fmt(orr['high'])} + {_fmt(orr['low'])}) / 2"
    lo, hi = i - 9, i + 1
    swing = float(lows[max(lo, 0):hi].min()) if side == "LONG" else float(highs[max(lo, 0):hi].max())
    stop = swing - s * 0.2 * a
    dist = (entry - stop) * s
    if a and a <= dist <= 3 * a:
        return stop, f"just {'below' if side == 'LONG' else 'above'} the 10-candle {'low' if side == 'LONG' else 'high'} {_fmt(swing)}"
    return entry - s * STOP_ATR * a, f"{STOP_ATR} × ATR ({_fmt(a)}) from the entry"


def _first_close_beyond(closes: np.ndarray, start: int, level: float, side: str) -> int | None:
    s = _sign(side)
    for i in range(start, len(closes)):
        if (closes[i] - level) * s > 0:
            return i
    return None


def entry_timer(df: pd.DataFrame, tf: str, side: str, horizon: int) -> list[dict]:
    """Every entry setup for this side: waiting (and how far), triggered (when, at what price), or expired."""
    s = _sign(side)
    closes, highs, lows = df["close"].values, df["high"].values, df["low"].values
    a = atr(df).values
    last = len(df) - 1
    out = []

    # Opening-range breakout of the UTC day (intraday timeframes only).
    if tf in OR_BARS:
        day = df.index[-1].floor("1D")
        orr = _opening_range(df, tf, day)
        if orr and not orr["complete"]:
            out.append({"setup": "orb", "name": "Opening-range breakout (UTC day)", "status": "FORMING",
                        "text": f"Today's opening range is still forming ({orr['bars']} of {orr['needed']} candles)."})
        elif orr:
            level = orr["high"] if side == "LONG" else orr["low"]
            start = int(df.index.searchsorted(orr["end"]))
            i = _first_close_beyond(closes, start, level, side)
            out.append(_state(df, tf, side, "orb", "Opening-range breakout (UTC day)", level, i, last, horizon,
                              a, lows, highs, orr))

    # Close beyond the 20-candle high / low (the scanner's breakout level, on this timeframe).
    if len(df) > LEVEL_LOOKBACK + 2:
        ext = pd.Series(highs if side == "LONG" else lows, index=df.index)
        ref = (ext.rolling(LEVEL_LOOKBACK).max() if side == "LONG" else ext.rolling(LEVEL_LOOKBACK).min()).shift().values
        trig = None
        for i in range(last, max(LEVEL_LOOKBACK, last - horizon), -1):
            if (closes[i] - ref[i]) * s > 0 and not (closes[i - 1] - ref[i - 1]) * s > 0:
                trig = i
                break
        level = float(ref[trig]) if trig is not None else float(
            (highs[-LEVEL_LOOKBACK:].max() if side == "LONG" else lows[-LEVEL_LOOKBACK:].min()))
        name = f"Close {'above the 20-candle high' if side == 'LONG' else 'below the 20-candle low'}"
        out.append(_state(df, tf, side, "level", name, level, trig, last, horizon, a, lows, highs, None))
    return out


def _state(df, tf, side, setup, name, level, i, last, horizon, a, lows, highs, orr) -> dict:
    s = _sign(side)
    closes = df["close"].values
    word = "above" if side == "LONG" else "below"
    base = {"setup": setup, "name": name, "level": level, "opening_range": (
        {"high": orr["high"], "low": orr["low"]} if orr else None)}
    if i is None:
        dist = (level - closes[-1]) * s
        return {**base, "status": "WAITING", "distance": dist, "distance_pct": dist / closes[-1] * 100,
                "distance_atr": dist / (a[-1] or 1e-12),
                "text": f"Waiting: last close {_fmt(closes[-1])} is {abs(dist / closes[-1] * 100):.2f}% "
                        f"({abs(dist / (a[-1] or 1e-12)):.1f} ATR) {'under' if side == 'LONG' else 'over'} the level "
                        f"{_fmt(level)}. Entry = the first {tf} candle that CLOSES {word} it."}
    stop, rule = _stop(a, lows, highs, i, side, float(closes[i]), setup, orr)
    t = df.index[i] + pd.Timedelta(seconds=TF_SECONDS[tf])
    after = closes[i + 1:]
    failed = bool(((after - stop) * s <= 0).any()) if len(after) else False
    age = last - i
    st = {**base, "status": "TRIGGERED", "bar_index": i, "bars_ago": age, "trigger_price": float(closes[i]),
          "trigger_time": int(t.timestamp()), "stop": stop, "stop_rule": rule}
    if failed:
        return {**st, "status": "EXPIRED", "text": f"Expired: it triggered at {_fmt(closes[i])} ({age} candles ago) "
                                                    f"but a later candle closed through the stop {_fmt(stop)}. The setup failed."}
    if age > horizon:
        return {**st, "status": "EXPIRED", "text": f"Expired: the trigger was {age} candles ago, the signal is stale."}
    when = "on the last closed candle" if age == 0 else f"{age} candle{'s' * (age > 1)} ago"
    return {**st, "text": f"Triggered {when}: a {tf} candle closed {word} {_fmt(level)} at {_fmt(closes[i])}."}


# ================================================================ 4. Time Machine (trader-timemachine)

def _ratios(df: pd.DataFrame) -> np.ndarray:
    prev = df["close"].shift().values
    r = np.column_stack([df["open"].values / prev, df["high"].values / prev, df["low"].values / prev,
                         df["close"].values / prev])[1:]
    return r[np.isfinite(r).all(axis=1)]


def _pools(df: pd.DataFrame, tf: str, start: pd.Timestamp, steps: int, window: int = 2):
    """Which past candles each replay step may draw from. With 20+ days of history a step only draws candles
    from the same time of day (±2 candles), like the Time Machine; otherwise from all recent candles."""
    ratios = _ratios(df)
    idx = df.index[1:][:len(ratios)]
    step_s = TF_SECONDS[tf]
    days = (df.index[-1] - df.index[0]).total_seconds() / 86400
    if tf in ("4h", "1d") or days < 20:
        return ratios, [np.arange(len(ratios))] * steps, "all recent candles (not enough days for time-of-day matching)"
    per_day = 86400 // step_s
    slot = ((idx.hour * 3600 + idx.minute * 60) // step_s).values
    pools = []
    for k in range(steps):
        target = int(((start.hour * 3600 + start.minute * 60) // step_s + k) % per_day)
        d = np.abs(slot - target)
        pools.append(np.where(np.minimum(d, per_day - d) <= window)[0])
    return ratios, pools, f"candles from the same time of day (±{window}) over {days:.0f} days"


def time_machine(df: pd.DataFrame, tf: str, side: str, entry: float, stop: float, target: float, steps: int,
                 replays: int = REPLAYS, seed: int = SEED, start: pd.Timestamp | None = None) -> dict:
    """Replay the next `steps` candles `replays` times from the coin's own candles. Stop is checked first:
    a candle that touches both counts as the stop, and a gap through the stop still counts as -1R."""
    s = _sign(side)
    risk = abs(entry - stop)
    if start is None:
        start = df.index[-1] + pd.Timedelta(seconds=TF_SECONDS[tf])
    ratios, pools, basis = _pools(df, tf, start, steps)
    if len(ratios) < 100:
        return {"error": "Not enough history for the replays"}
    pools = [p if len(p) >= 10 else np.arange(len(ratios)) for p in pools]
    rng = np.random.default_rng(seed)
    price = np.full(replays, entry)
    state = np.zeros(replays, dtype=int)
    fan = []
    for k in range(steps):
        pick = ratios[pools[k][rng.integers(0, len(pools[k]), replays)]]
        hi, lo, cl = pick[:, 1] * price, pick[:, 2] * price, pick[:, 3] * price
        live = state == 0
        hit_stop = (lo <= stop) if side == "LONG" else (hi >= stop)
        hit_tgt = (hi >= target) if side == "LONG" else (lo <= target)
        state[live & hit_stop] = -1
        state[live & ~hit_stop & hit_tgt] = 1
        price = cl
        fan.append([float(q) for q in np.percentile(price, [5, 25, 50, 75, 95])])
    r_target = abs(target - entry) / risk
    r = np.where(state == 1, r_target, np.where(state == -1, -1.0, (price - entry) * s / risk))
    fee_r = 2 * FEE * entry / risk
    mc = {"replays": replays, "seed": seed, "steps": steps, "basis": basis, "r_at_target": r_target,
          "p_target": float((state == 1).mean()), "p_stop": float((state == -1).mean()),
          "p_neither": float((state == 0).mean()),
          "p_green": float(((state == 1) | ((state == 0) & ((price - entry) * s > 0))).mean()),
          "end_median": float(np.median(price)), "end_p5": float(np.percentile(price, 5)),
          "end_p95": float(np.percentile(price, 95)), "avg_r": float(r.mean()), "fee_r": fee_r,
          "avg_r_after_fees": float(r.mean() - fee_r), "fan": fan}
    mc["verdict"], mc["lean"] = verdict(mc)
    mc["notes"] = verdict_notes(mc, steps, tf)
    return mc


def lean(mc: dict):
    pt, ps = mc["p_target"], mc["p_stop"]
    if pt + ps <= 0:
        return None
    share, even = pt / (pt + ps), 1 / (1 + (mc.get("r_at_target") or 1.0))
    return share - even, share, even


def verdict(mc: dict) -> tuple[str, str]:
    """The Time Machine's one line: is the target's share of decided replays above its break-even 1/(1+R)?"""
    lv = lean(mc)
    if lv is None:
        return "No replay reached the target or the stop: the price at the end decides every one.", "NONE"
    d, share, even = lv
    r = mc["r_at_target"]
    one_r = abs(r - 1) < 0.005
    if abs(d) < COIN_FLIP:
        head, tag = ("Close to a coin flip" if one_r else "Close to break-even"), "EVEN"
    elif abs(d) < STRONG:
        head, tag = ("Leans toward the target", "TARGET") if d > 0 else ("Leans toward the stop", "STOP")
    else:
        head, tag = ("Strongly toward the target", "STRONG_TARGET") if d > 0 else ("Strongly toward the stop", "STRONG_STOP")
    odds = f"target first {mc['p_target'] * 100:.1f}% vs stop first {mc['p_stop'] * 100:.1f}%"
    if one_r:
        return f"{head}: {odds}.", tag
    return (f"{head}: at {r:.2g}R the target has to come first in {even * 100:.0f}% of the replays that hit one "
            f"side; it did in {share * 100:.0f}% ({odds})."), tag


def verdict_notes(mc: dict, steps: int, tf: str) -> list[str]:
    notes = []
    lv = lean(mc)
    if mc["p_neither"] > MANY_NEITHER and lv is not None:
        notes.append(f"{mc['p_neither'] * 100:.1f}% of the replays hit neither within {steps} × {tf}; "
                     "the price at the end decides those.")
    if lv and abs(lv[0]) >= COIN_FLIP and mc["avg_r"] and (mc["avg_r"] > 0) != (lv[0] > 0):
        notes.append(f"Average R is {mc['avg_r']:+.3f} all the same: the replays that hit neither pull it the other way.")
    return notes


def history(df: pd.DataFrame, tf: str, side: str, setup: str, target_r: float, steps: int) -> dict:
    """The same rule on every past occasion it fired in the data: what really happened, not a simulation."""
    s = _sign(side)
    closes, highs, lows = df["close"].values, df["high"].values, df["low"].values
    a = atr(df).values
    trades = []  # (entry index, entry, stop)
    if setup == "orb":
        for day in pd.unique(df.index.floor("1D")):
            orr = _opening_range(df, tf, pd.Timestamp(day))
            if not orr or not orr["complete"]:
                continue
            level = orr["high"] if side == "LONG" else orr["low"]
            begin = int(df.index.searchsorted(orr["end"]))
            end = int(df.index.searchsorted((pd.Timestamp(day) + pd.Timedelta(days=1))))
            i = _first_close_beyond(closes[:end], begin, level, side)
            if i is not None:
                trades.append((i, float(closes[i]), _stop(a, lows, highs, i, side, float(closes[i]), "orb", orr)[0]))
    else:
        ext = pd.Series(highs if side == "LONG" else lows)
        ref = (ext.rolling(LEVEL_LOOKBACK).max() if side == "LONG" else ext.rolling(LEVEL_LOOKBACK).min()).shift().values
        free = 0
        for i in range(LEVEL_LOOKBACK + 15, len(df)):
            if i >= free and (closes[i] - ref[i]) * s > 0 and not (closes[i - 1] - ref[i - 1]) * s > 0:
                st = _stop(a, lows, highs, i, side, float(closes[i]), "level", None)[0]
                trades.append((i, float(closes[i]), st))
                free = i + steps
    res = {"target": 0, "stop": 0, "neither": 0, "r": []}
    last_full = len(df) - 1 - steps
    for i, entry, stop in trades:
        if i > last_full:
            continue  # not enough candles after it to know the outcome yet
        risk = abs(entry - stop)
        target = entry + s * target_r * risk
        out = None
        for j in range(i + 1, i + 1 + steps):
            if (lows[j] <= stop) if side == "LONG" else (highs[j] >= stop):
                out = "stop"
                break
            if (highs[j] >= target) if side == "LONG" else (lows[j] <= target):
                out = "target"
                break
        if out is None:
            res["neither"] += 1
            res["r"].append((closes[i + steps] - entry) * s / risk)
        else:
            res[out] += 1
            res["r"].append(target_r if out == "target" else -1.0)
    n = len(res["r"])
    return {"fired": n, "target": res["target"], "stop": res["stop"], "neither": res["neither"],
            "avg_r": float(np.mean(res["r"])) if n else None,
            "text": (f"The same rule fired {n} times in the last {len(df)} {tf} candles: {res['target']} hit the target, "
                     f"{res['stop']} the stop, {res['neither']} neither. Average R {np.mean(res['r']):+.2f}."
                     if n else f"The same rule hasn't fired with a known outcome in the last {len(df)} {tf} candles.")}


# ================================================================ 5. account protection

def circuit_breaker(journal: dict | None, tf: str, now: float) -> dict:
    """drawdown-circuit-breaker on the demo account's closed trades: daily / weekly / monthly loss limits and
    a cool-down after a losing streak."""
    rules = RULES["intraday" if tf in INTRADAY else "swing"]
    trades = sorted((journal or {}).get("trades") or [], key=lambda t: t.get("closed", 0))
    equity = float((journal or {}).get("start_equity") or 0)
    if not trades or equity <= 0:
        return {"recommendation": "TRADING_ALLOWED", "rules": [], "metrics": {}, "data": "no closed trades yet",
                "streak": 0}
    t_now = pd.Timestamp(now, unit="s", tz="UTC")
    day = t_now.floor("1D")
    week = day - pd.Timedelta(days=day.weekday())
    month = day.replace(day=1)
    pnl = {"today": 0.0, "week": 0.0, "month": 0.0}
    for t in trades:
        ts = pd.Timestamp(t["closed"] / 1000, unit="s", tz="UTC")
        p = float(t.get("pnl", 0))
        pnl["month"] += p if ts >= month else 0
        pnl["week"] += p if ts >= week else 0
        pnl["today"] += p if ts >= day else 0
    streak = 0
    for t in reversed(trades):
        if float(t.get("pnl", 0)) < 0:
            streak += 1
        else:
            break
    triggered = []
    for label, key, lim, until in (("Daily loss", "today", DAILY_LOSS_PCT, day + pd.Timedelta(days=1)),
                                   ("Weekly drawdown", "week", WEEKLY_LOSS_PCT, week + pd.Timedelta(days=7)),
                                   ("Monthly drawdown", "month", MONTHLY_LOSS_PCT, month + pd.offsets.MonthBegin(1))):
        pct = -pnl[key] / equity * 100
        if pct >= lim:
            triggered.append({"rule": label, "state": "HALTED", "until": int(until.timestamp()),
                              "detail": f"{label} {pct:.2f}% of the account (limit {lim}%)"})
    if streak >= rules["losing_streak"]:
        until = trades[-1]["closed"] / 1000 + rules["cooldown_hours"] * 3600
        if now < until:
            triggered.append({"rule": "Losing streak", "state": "COOLDOWN", "until": int(until),
                              "detail": f"{streak} losses in a row: cool down for {rules['cooldown_hours']} h after the last one"})
    rec = "HALTED" if any(r["state"] == "HALTED" for r in triggered) else "COOLDOWN" if triggered else "TRADING_ALLOWED"
    return {"recommendation": rec, "rules": triggered, "streak": streak,
            "metrics": {k: round(v / equity * 100, 3) for k, v in pnl.items()}}


# ================================================================ the whole plan

def build_plan(snap: MarketSnapshot, decision, forecast: dict | None = None, *, account: float = 1000.0,
               risk_pct: float = 1.0, side: str = "AUTO", target_r: float = 2.0, min_rr: float = 1.5,
               max_leverage: float = 5.0, coin_daily: pd.DataFrame | None = None,
               btc_daily: pd.DataFrame | None = None, journal: dict | None = None,
               now: float | None = None, replays: int = REPLAYS) -> dict:
    now = time.time() if now is None else now
    tf = snap.entry_timeframe
    df = _closed(snap.candles[tf], tf, now)
    if len(df) < 120:
        return {"error": f"Not enough {tf} history for a trade plan ({len(df)} closed candles, need 120)."}
    live_price = float(snap.candles[tf]["close"].iloc[-1])
    horizon = HORIZON.get(tf, 20)
    by_agent = {r.agent: r for r in decision.reports}
    trend = by_agent.get("Trend Analyst")
    side = side.upper() if side and side.upper() in ("LONG", "SHORT") else ("LONG" if decision.score >= 0 else "SHORT")
    s = _sign(side)
    steps, warnings = [], []

    # 1. Market regime
    reg = market_regime(snap, coin_daily, btc_daily)
    size_factor = 1.0
    against = (reg["zone"] == "RISK_OFF" and side == "LONG") or (reg["zone"] == "RISK_ON" and side == "SHORT")
    if reg["score"] is None:
        st, summ = "INFO", reg["posture"]
    elif against:
        size_factor = 0.5
        st, summ = "WARN", f"{reg['zone']} ({reg['score']:.0f}/100) works against a {side}: size is cut in half."
    else:
        st, summ = "PASS", f"{reg['zone']} ({reg['score']:.0f}/100). {reg['posture']}"
    steps.append(_step("regime", "Market regime", "crypto-regime-analyzer", st, summ,
                       [f"{c['name']} ({c['weight']}%): {c['score']:.0f}/100, {c['signal']}" for c in reg["components"]], reg))

    # 2. Multi-timeframe technical confluence (the agents)
    opp = trend is not None and trend.score * s < -0.15
    if decision.action == side:
        st, summ = "PASS", f"The Chief Strategist says {side}: {decision.reasons[-1] if decision.reasons else ''}"
    elif decision.action == "NO TRADE" and not opp:
        st, summ = "WARN", f"The agents lean {side} (score {decision.score:+.2f}) but there's no confirmed signal yet."
    else:
        st, summ = "FAIL", (f"The agents say {decision.action}, and the higher-timeframe trend is against a {side}."
                            if opp else f"The agents say {decision.action}.")
    det = [f"{r.agent}: {r.bias} {r.score:+.2f}, {r.summary}" for r in decision.reports if r.agent != "Risk Manager"]
    det.append(f"Strategy for this market: {decision.strategy}. {decision.playbook}")
    steps.append(_step("technicals", "Multi-timeframe analysis", "technical-analyst + the agent team", st, summ, det,
                       {"action": decision.action, "score": decision.score}))
    confluence = st

    # 3. Setups on the chart
    setups = scan_setups(df)
    mine = [x for x in setups if x["bias"] == side]
    against_setups = [x for x in setups if x["bias"] != side]
    steps.append(_step("setups", "Setup scanner", "trader-scanner", "PASS" if mine else "INFO",
                       (f"{len(mine)} {side} setup{'s' * (len(mine) != 1)} on the chart: " + ", ".join(x["name"] for x in mine))
                       if mine else f"No classic {side} setup on the last candle.",
                       [f"{'✔' if x['bias'] == side else '✖'} {x['name']} ({x['bias']}): {x['detail']}" for x in setups],
                       {"setups": setups}))
    if against_setups:
        warnings.append("Setups against this trade: " + ", ".join(x["name"] for x in against_setups))

    # 4. Entry timer: pick the setup that is actionable now (fresh trigger first, else the nearest level)
    states = entry_timer(df, tf, side, horizon)
    usable = [x for x in states if x["status"] in ("TRIGGERED", "WAITING")]
    fresh = [x for x in usable if x["status"] == "TRIGGERED"]
    if fresh:
        chosen = min(fresh, key=lambda x: x["bars_ago"])
    elif usable:
        chosen = min(usable, key=lambda x: abs(x.get("distance_atr", 1e9)))
    else:
        chosen = states[0] if states else None
    if chosen is None:
        return {"error": "No entry setup could be built from this data."}

    # 5. Exit plan: stop and target set BEFORE the entry
    a_now = float(atr(df).iloc[-1])
    closes, highs, lows = df["close"].values, df["high"].values, df["low"].values
    late = False
    if chosen["status"] == "TRIGGERED" and (live_price - chosen["level"]) * s <= 0:
        # It broke out, then fell back through the level: that breakout is spent, it needs a new close beyond.
        chosen = {**chosen, "status": "WAITING", "text": f"It triggered {chosen['bars_ago']} candles ago but price is back "
                  f"{'under' if side == 'LONG' else 'over'} {_fmt(chosen['level'])}: it needs a new close beyond it."}
    if chosen["status"] == "TRIGGERED":
        stop, stop_rule = chosen["stop"], chosen["stop_rule"]
        trig = chosen["trigger_price"]
        late = (live_price - trig) * s > CHASE_R * abs(trig - stop) or chosen["bars_ago"] > 1
        entry = live_price
        entry_kind = "market"
        if late:  # don't chase: a limit order back at the broken level (the retest), with its own stop
            entry, entry_kind = chosen["level"], "retest limit"
            stop, stop_rule = _stop(atr(df).values, lows, highs, len(df) - 1, side, entry, chosen["setup"],
                                    chosen.get("opening_range"))
    else:
        entry = chosen.get("level", live_price)
        entry_kind = "on close beyond the level"
        stop, stop_rule = _stop(atr(df).values, lows, highs, len(df) - 1, side, entry, chosen["setup"],
                                chosen.get("opening_range"))
    entry = _round(entry, entry)
    stop = _round(stop, entry, away_from=entry)
    risk = abs(entry - stop)
    risk_pct_price = risk / entry * 100 if entry else 0
    spread = (snap.orderflow or {}).get("spread_pct") or 0
    refused = []
    if (entry - stop) * s <= 0:
        refused.append("the stop is on the wrong side of the entry")
    if risk_pct_price < max(MIN_RISK_PCT, 3 * spread):
        refused.append(f"the stop is only {risk_pct_price:.3f}% away: too tight to survive the spread and normal wiggle")
    if risk_pct_price > MAX_RISK_PCT:
        refused.append(f"the stop is {risk_pct_price:.1f}% away: wider than the {MAX_RISK_PCT:.0f}% maximum")
    targets = [_round(entry + s * r * risk, entry) for r in (1.0, target_r, target_r + 1)]
    target = targets[1]
    structure = by_agent.get("Price Action & Volume Analyst")
    wall = (structure.data.get("resistance") if side == "LONG" else structure.data.get("support")) if structure else None
    if wall and 0 < (wall - entry) * s < (target - entry) * s:
        warnings.append(f"{'Resistance' if side == 'LONG' else 'Support'} at {_fmt(wall)} sits before the "
                        f"{target_r:g}R target: expect a fight there, consider taking profit early.")
    exit_plan = {"entry": entry, "entry_kind": entry_kind, "stop": stop, "stop_rule": stop_rule, "risk_per_unit": risk,
                 "risk_pct": risk_pct_price, "targets": targets, "target_r": target_r,
                 "reward_risk": target_r, "expires_after": f"{horizon} × {tf} candles", "refused": refused}
    steps.append(_step("exit", "Exit plan (set before the entry)", "trader-exit", "FAIL" if refused else "PASS",
                       (f"Refused: {'; '.join(refused)}." if refused else
                        f"Stop {_fmt(stop)} ({risk_pct_price:.2f}% away, {stop_rule}); target {_fmt(target)} ({target_r:g}R)."),
                       [f"Entry {_fmt(entry)} ({entry_kind})", f"Stop {_fmt(stop)}: {stop_rule}",
                        f"Take profit: 1R {_fmt(targets[0])} (take half, move the stop to break-even), "
                        f"{target_r:g}R {_fmt(targets[1])}, {target_r + 1:g}R {_fmt(targets[2])} (runner)",
                        "A stop is a plan, not a guarantee: a fast market can fill past it."], exit_plan))

    # 6. Time Machine: the plan replayed 10,000 times + the same rule on past data
    tm = time_machine(df, tf, side, entry, stop, target, horizon, replays=replays) if not refused else \
        {"error": "Skipped: the exit plan was refused."}
    hist = history(df, tf, side, chosen["setup"], target_r, horizon)
    if tm.get("error"):
        st, summ, det = "INFO", tm["error"], []
    else:
        tag = tm["lean"]
        st = "FAIL" if tag == "STRONG_STOP" else "WARN" if tag in ("STOP", "EVEN", "NONE") else "PASS"
        summ = tm["verdict"]
        det = [f"{tm['replays']:,} replays of the next {horizon} × {tf} candles (seed {tm['seed']}), drawn from {tm['basis']}",
               f"Target first {tm['p_target']:.1%} · stop first {tm['p_stop']:.1%} · neither {tm['p_neither']:.1%} · "
               f"in profit at the end {tm['p_green']:.1%}",
               f"Price after {horizon} candles: median {_fmt(tm['end_median'])}, 90% between {_fmt(tm['end_p5'])} "
               f"and {_fmt(tm['end_p95'])}",
               f"Average R {tm['avg_r']:+.3f}, after fees {tm['avg_r_after_fees']:+.3f} (fees cost {tm['fee_r']:.3f}R)",
               *tm["notes"], hist["text"],
               "This is a simulation built from this coin's recent candles, not a prediction. News can do things those candles never did."]
        if hist["fired"] >= 10 and hist["avg_r"] is not None and (hist["avg_r"] > 0) != (tm["avg_r"] > 0):
            det.append("The real history and the replays disagree: treat the edge as unproven.")
    if st == "WARN" and tm.get("lean") == "STOP":
        warnings.append("The Time Machine leans toward the stop: skip it or trade smaller.")
    steps.append(_step("timemachine", "Time Machine", "trader-timemachine", st, summ, det, {"mc": tm, "history": hist}))
    tm_status = st

    # 7. Position size
    risk_budget = account * risk_pct / 100 * size_factor
    loss_per_unit = risk + FEE * (entry + stop)
    units = risk_budget / loss_per_unit if loss_per_unit > 0 else 0.0
    if units > 0:
        q = 10 ** (math.floor(math.log10(units)) - 3)
        units = math.floor(units / q) * q
    value = units * entry
    lev = value / account if account else 0
    capped = lev > max_leverage
    if capped:
        units = account * max_leverage / entry
        value, lev = units * entry, max_leverage
    max_loss = units * loss_per_unit
    sizing = {"units": units, "value": value, "leverage": max(1.0, math.ceil(lev * 10) / 10), "max_loss": max_loss,
              "risk_budget": risk_budget, "size_factor": size_factor, "margin": value / max(1.0, math.ceil(lev * 10) / 10)}
    steps.append(_step("size", "Position size", "trader-budget + position-sizer", "WARN" if capped else "PASS",
                       f"{units:.6g} {snap.symbol.replace('USDT', '')} ≈ {value:,.2f} USDT; loss at the stop "
                       f"{max_loss:,.2f} USDT including fees ({max_loss / account * 100:.2f}% of the account).",
                       [f"Risk budget {risk_pct:g}% of {account:,.0f} = {account * risk_pct / 100:,.2f} USDT"
                        + (" × 0.5 (against the regime)" if size_factor < 1 else ""),
                        f"Loss per unit at the stop {_fmt(loss_per_unit)} (risk {_fmt(risk)} + fees)",
                        f"Needs {sizing['leverage']:g}x leverage (margin ≈ {sizing['margin']:,.2f} USDT)"
                        + (f": capped at {max_leverage:g}x, so the size is smaller than the risk allows" if capped else "")],
                       sizing))

    # 8. Risk manager limits
    rules = RULES["intraday" if tf in INTRADAY else "swing"]
    j = journal or {}
    today = pd.Timestamp(now, unit="s", tz="UTC").floor("1D").timestamp() * 1000
    eq = float(j.get("start_equity") or 0)
    today_trades = [t for t in j.get("trades") or [] if t.get("closed", 0) >= today]
    lost_today_pct = -sum(min(0.0, float(t.get("pnl", 0))) for t in today_trades) / eq * 100 if eq else 0.0
    open_syms = set(j.get("open_symbols") or [])
    checks = [
        ("stop", not refused and (entry - stop) * s > 0, f"stop {_fmt(stop)} is set before the entry"),
        ("loss", max_loss <= account * risk_pct / 100 * 1.0001, f"loss at the stop {max_loss:,.2f} ≤ max {account * risk_pct / 100:,.2f}"),
        ("reward:risk", target_r >= min_rr, f"reward:risk {target_r:g} (min {min_rr:g})"),
        ("width", MIN_RISK_PCT <= risk_pct_price <= MAX_RISK_PCT, f"stop {risk_pct_price:.2f}% away (allowed {MIN_RISK_PCT}–{MAX_RISK_PCT:.0f}%)"),
        ("daily loss", lost_today_pct + risk_pct * size_factor <= 3 * risk_pct,
         f"lost today {lost_today_pct:.2f}% + this trade {risk_pct * size_factor:.2f}% ≤ daily limit {3 * risk_pct:g}%"),
        ("trades", len(today_trades) < rules["max_trades_per_day"],
         f"{len(today_trades)} of {rules['max_trades_per_day']} trades used today"),
        ("duplicate", snap.symbol not in open_syms, f"no open {snap.symbol} position" if snap.symbol not in open_syms
         else f"you already have an open {snap.symbol} position"),
        ("volatility", (by_agent.get("Risk Manager").confidence if by_agent.get("Risk Manager") else 1) >= 0.2,
         by_agent["Risk Manager"].summary if by_agent.get("Risk Manager") else "volatility unknown"),
    ]
    blocked = [c for c in checks if not c[1]]
    steps.append(_step("risk", "Risk manager", "trader-risk", "FAIL" if blocked else "PASS",
                       ("BLOCK: " + "; ".join(c[2] for c in blocked)) if blocked else "PASS: the order fits every limit.",
                       [f"{'PASS' if ok else 'BLOCK'} {name}: {txt}" for name, ok, txt in checks]))

    # 9. Drawdown circuit breaker
    cb = circuit_breaker(journal, tf, now)
    steps.append(_step("breaker", "Drawdown circuit breaker", "drawdown-circuit-breaker",
                       "PASS" if cb["recommendation"] == "TRADING_ALLOWED" else "FAIL",
                       {"TRADING_ALLOWED": "Trading allowed: no loss limit or cool-down is active.",
                        "COOLDOWN": "COOLDOWN: no new positions until the cool-down ends.",
                        "HALTED": "HALTED: a loss limit was hit, no new entries."}[cb["recommendation"]],
                       [r["detail"] + f" (until {pd.Timestamp(r['until'], unit='s', tz='UTC'):%Y-%m-%d %H:%M} UTC)" for r in cb["rules"]]
                       + ([f"Demo account P&L: today {cb['metrics']['today']:+.2f}%, this week {cb['metrics']['week']:+.2f}%, "
                           f"this month {cb['metrics']['month']:+.2f}% · losing streak {cb['streak']}"] if cb["metrics"] else
                          ["Reads your demo account's closed trades (none yet)."]), cb))

    # 10. Pre-trade discipline gate
    revenge = [t for t in j.get("trades") or [] if float(t.get("pnl", 0)) < 0
               and now - t.get("closed", 0) / 1000 < rules["revenge_minutes"] * 60]
    gate = [("Entry is in a written plan", True), ("Stop is set before the entry", not refused),
            ("Size is within the plan", max_loss <= risk_budget * 1.0001 or capped),
            (f"No loss in the last {rules['revenge_minutes'] // 60 or rules['revenge_minutes']}"
             f"{' h' if rules['revenge_minutes'] >= 60 else ' min'} (revenge-trade check)", not revenge),
            ("Circuit breaker allows trading", cb["recommendation"] == "TRADING_ALLOWED")]
    bad = [g for g, ok in gate if not ok]
    steps.append(_step("gate", "Pre-trade discipline gate", "pre-trade-discipline-gate", "FAIL" if bad else "PASS",
                       ("NO_GO: " + "; ".join(bad)) if bad else "GO: every discipline check passed.",
                       [f"{'✔' if ok else '✖'} {g}" for g, ok in gate]))

    # 11. Next-candle forecast cross-check (optional)
    if forecast and not forecast.get("error"):
        fc = forecast.get("final_call")
        if fc == side:
            st, summ = "PASS", f"The next-candle council agrees: {fc} {forecast['chance']:.0%} ({forecast['strength']})."
        elif fc in ("LONG", "SHORT"):
            st, summ = "WARN", f"The next-candle council says {fc} ({forecast['strength']}): the first candle may go against you."
        else:
            st, summ = "INFO", f"The next-candle council has no strong view (leans {forecast.get('direction')})."
        steps.append(_step("forecast", "Next-candle check", "agent council", st, summ))

    # The verdict: where (and whether) to enter
    blockers = [x for x in steps if x["status"] == "FAIL"]
    hard = [x for x in blockers if x["key"] in ("risk", "breaker", "gate", "exit", "technicals", "timemachine")]
    word = "above" if side == "LONG" else "below"
    base = snap.symbol.replace("USDT", "")
    if chosen["status"] == "EXPIRED" and not usable:
        action, headline = "NO TRADE", "The setup already failed. Wait for a new one."
    elif hard:
        action, headline = "NO TRADE", "Blocked by: " + ", ".join(x["title"].lower() for x in hard) + "."
    elif chosen["status"] == "TRIGGERED" and not late:
        action, headline = f"ENTER {side} NOW", (f"The {chosen['name'].lower()} triggered. Enter at about {_fmt(entry)}, "
                                                 f"no worse than {_fmt(chosen['trigger_price'] + s * CHASE_R * abs(chosen['trigger_price'] - stop))}.")
    elif chosen["status"] == "TRIGGERED":
        action, headline = f"WAIT FOR RETEST ({side})", (f"It already moved without you. Don't chase: place a limit {side} at "
                                                          f"the retest of {_fmt(entry)}.")
    else:
        action, headline = f"WAIT FOR {side} TRIGGER", (f"Enter {side} only when a {tf} candle CLOSES {word} {_fmt(entry)}. "
                                                        "Not before.")
    how = []
    if not action.startswith("NO TRADE"):
        if action.startswith("WAIT FOR " + side):
            how += [f"Set a price alert at {_fmt(entry)}.",
                    f"Wait for a {tf} candle to CLOSE {word} {_fmt(entry)}. A wick through it is not an entry.",
                    f"Enter {side} at that close, no worse than {_fmt(entry + s * CHASE_R * risk)} (half the risk past the level)."]
        elif action.startswith("WAIT FOR RETEST"):
            how += [f"Place a limit {'buy' if side == 'LONG' else 'sell'} at {_fmt(entry)} (the broken level).",
                    "If price never comes back, you skip this trade. That is fine."]
        else:
            how.append(f"{'Buy' if side == 'LONG' else 'Sell short'} {units:.6g} {base} now at about {_fmt(entry)}.")
        how += [f"Place the stop-loss at {_fmt(stop)} immediately ({stop_rule}).",
                f"Take half off at {_fmt(targets[0])} (1R) and move the stop to break-even; "
                f"take the rest at {_fmt(targets[1])} ({target_r:g}R).",
                f"Size: {units:.6g} {base} (≈ {value:,.2f} USDT, {sizing['leverage']:g}x); "
                f"the most you lose at the stop is {max_loss:,.2f} USDT.",
                f"The plan expires after {horizon} {tf} candles, or if a candle closes through the stop first."]
    else:
        how.append("Stay flat. Re-check at the next candle close; the plan updates automatically.")
        if chosen["status"] == "WAITING":
            how.append(f"The level to watch is {_fmt(chosen['level'])}: a {tf} close {word} it would build a new plan.")
    if forecast and forecast.get("final_call") in ("LONG", "SHORT") and forecast["final_call"] != side:
        warnings.append("The next-candle forecast points the other way.")
    passed = sum(x["status"] == "PASS" for x in steps)
    return {
        "symbol": snap.symbol, "timeframe": tf, "side": side, "action": action, "headline": headline,
        "how_to_enter": how, "price": live_price, "entry": entry, "entry_kind": entry_kind, "stop": stop,
        "targets": targets, "target_r": target_r, "sizing": sizing, "setup": chosen, "setups_state": states,
        "steps": steps, "warnings": warnings + list(snap.notes), "score": f"{passed} of {len(steps)} checks passed",
        "generated_at": now, "atr": a_now,
        "disclaimer": "A plan is a rules check, not a promise. No setup wins every time; most day traders lose money. "
                      "Nothing was ordered. Paper-trade it first.",
    }
