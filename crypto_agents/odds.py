"""Honest win/loss odds: replay the agents over the most recent candles of the SAME coin and timeframe
and measure what actually happened after each signal.

No sentiment or order-book history is available for the past, so the replay uses the technical agents
plus candle taker-flow. The numbers describe recent behaviour, not a guarantee of the next trade.
"""
from __future__ import annotations

import math

import pandas as pd

from .data import TF_SECONDS, MarketSnapshot
from .strategist import HORIZON, Strategist


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a win rate — small samples give wide ranges, as they should."""
    if n == 0:
        return 0.0, 1.0
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _simulate(plan, future: pd.DataFrame) -> tuple[str, float]:
    sign = 1 if plan.direction == "LONG" else -1
    tp = plan.take_profits[0]
    for _, bar in future.iterrows():
        hit_stop = bar.low <= plan.stop_loss if sign > 0 else bar.high >= plan.stop_loss
        hit_tp = bar.high >= tp if sign > 0 else bar.low <= tp
        if hit_stop:  # pessimistic: if both hit in one candle, count the loss
            return "loss", -1.0
        if hit_tp:
            return "win", abs(tp - plan.entry) / plan.risk_per_unit
    r = sign * (future.close.iloc[-1] - plan.entry) / plan.risk_per_unit
    return "timeout", float(r)


def historical_odds(snap: MarketSnapshot, current_score: float, current_action: str,
                    strategist: Strategist | None = None, samples: int = 120) -> dict:
    strategist = strategist or Strategist()
    tf = snap.entry_timeframe
    step = pd.Timedelta(seconds=TF_SECONDS[tf])
    horizon = HORIZON.get(tf, 20)
    closed = snap.candles[tf].iloc[:-1]  # the last candle may still be forming
    n = len(closed)
    start, end = max(220, n - samples - horizon), n - horizon
    if start >= end:
        return {"error": "Not enough history to measure odds"}

    records, trades = [], []
    for t in range(start, end):
        cutoff = closed.index[t] + step
        candles = {}
        for htf, df in snap.candles.items():
            if htf == tf:
                candles[tf] = closed.iloc[: t + 1]
            else:  # only higher-timeframe candles that had fully closed at that moment
                candles[htf] = df[df.index + pd.Timedelta(seconds=TF_SECONDS[htf]) <= cutoff]
        d = strategist.decide(MarketSnapshot(snap.symbol, candles))
        future = closed.iloc[t + 1: t + 1 + horizon]
        records.append((d.score, future.close.iloc[-1] > closed.close.iloc[t]))
        if d.plan is not None:
            outcome, r = _simulate(d.plan, future)
            trades.append({"direction": d.plan.direction, "outcome": outcome, "r": r})

    # Direction odds: how often price was higher after the horizon when the agents scored similarly.
    similar = [up for s, up in records if abs(s - current_score) <= 0.15]
    basis = "similar combined score (±0.15)"
    if len(similar) < 15:
        similar = [up for s, up in records if (s > 0) == (current_score > 0)]
        basis = "same score direction"
    base_up = sum(up for _, up in records) / len(records)
    p_up = sum(similar) / len(similar) if similar else base_up

    def stats(rows):
        wins = sum(r["outcome"] == "win" for r in rows)
        losses = sum(r["outcome"] == "loss" for r in rows)
        lo, hi = wilson(wins, len(rows))
        return {"signals": len(rows), "wins": wins, "losses": losses,
                "timeouts": len(rows) - wins - losses,
                "win_rate": wins / len(rows) if rows else None,
                "win_rate_95ci": [lo, hi] if rows else None,
                "avg_r": sum(r["r"] for r in rows) / len(rows) if rows else None}

    same_dir = [r for r in trades if r["direction"] == current_action]
    first, last = closed.index[start], closed.index[end - 1]
    return {
        "timeframe": tf, "horizon_candles": horizon, "windows_tested": len(records),
        "period": f"{first:%Y-%m-%d %H:%M} → {last:%Y-%m-%d %H:%M} UTC",
        "chance_up": p_up, "chance_down": 1 - p_up, "chance_basis": basis, "chance_samples": len(similar),
        "base_rate_up": base_up,
        "all_signals": stats(trades),
        "same_direction": stats(same_dir) if current_action in ("LONG", "SHORT") else None,
        "target": "TP1 (1.5R) before stop-loss",
        "note": "Measured on this coin's own recent candles. Small samples are unreliable; "
                "past results do not guarantee the next trade.",
    }
