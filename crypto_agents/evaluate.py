"""Walk-forward test on real candles: replay history and score every Chief call against what really happened."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data
from .forecast import next_candle
from .odds import wilson
from .strategist import Strategist


def evaluate(candles: pd.DataFrame, timeframe: str, predictions: int = 300, fee_round_trip_pct: float = 0.08,
             symbol: str = "TEST", history: int = 2500) -> dict:
    """Predict each of the last `predictions` candles using only earlier candles, then grade it."""
    sec = data.TF_SECONDS[timeframe]
    start = max(300, len(candles) - predictions)
    strat = Strategist()
    calls, leans = [], []
    for t in range(start, len(candles)):
        hist = candles.iloc[max(0, t - history):t]
        snap = data.snapshot_from_base(symbol, hist, timeframe)
        f = next_candle(snap, strat.decide(snap), now=hist.index[-1].timestamp() + 2 * sec)
        if "error" in f:
            continue
        move = candles["close"].iloc[t] / candles["close"].iloc[t - 1] - 1
        if move == 0:
            continue
        leans.append((f["direction"] == "LONG") == (move > 0))
        if f["final_call"] != "NO TRADE":
            calls.append(move if f["final_call"] == "LONG" else -move)
    r = np.array(calls)
    wins = int((r > 0).sum())
    lo, hi = wilson(wins, len(r))
    net = r - fee_round_trip_pct / 100
    return {
        "candles_tested": len(leans),
        "lean_accuracy": float(np.mean(leans)) if leans else None,
        "chief_calls": len(r), "chief_accuracy": wins / len(r) if len(r) else None, "chief_accuracy_95ci": [lo, hi],
        "avg_move_per_call_pct": float(r.mean() * 100) if len(r) else None,
        "equity_no_fees": float(100000 * np.prod(1 + r)), "equity_after_fees": float(100000 * np.prod(1 + net)),
        "fee_round_trip_pct": fee_round_trip_pct,
    }
