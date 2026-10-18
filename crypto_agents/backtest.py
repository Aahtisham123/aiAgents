"""Walk-forward backtest: replays history candle by candle so you can see the REAL win rate."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .data import snapshot_from_hourly
from .strategist import Strategist


@dataclass
class BacktestResult:
    trades: pd.DataFrame

    @property
    def summary(self) -> dict:
        t = self.trades
        if t.empty:
            return {"trades": 0}
        wins = t[t.r > 0]
        losses = t[t.r <= 0]
        equity = t.r.cumsum()
        return {
            "trades": len(t),
            "win_rate_%": round(100 * len(wins) / len(t), 1),
            "avg_R_per_trade": round(t.r.mean(), 3),
            "total_R": round(t.r.sum(), 2),
            "profit_factor": round(wins.r.sum() / abs(losses.r.sum()), 2) if len(losses) else float("inf"),
            "max_drawdown_R": round((equity.cummax() - equity).max(), 2),
            "longs": int((t.direction == "LONG").sum()),
            "shorts": int((t.direction == "SHORT").sum()),
        }


def backtest(hourly: pd.DataFrame, symbol: str = "BACKTEST", strategist: Strategist | None = None,
             step: int = 4, warmup: int = 24 * 220, target_r: float = 2.0, max_hold: int = 72) -> BacktestResult:
    """Every `step` hours ask the strategist for a decision using only past data, then simulate the trade.

    A trade exits at the stop (-1R), at `target_r`, or at market after `max_hold` candles.
    If the stop and target are both touched inside one candle we assume the stop hit first (pessimistic).
    """
    strategist = strategist or Strategist()
    rows, i = [], warmup
    while i < len(hourly) - 1:
        snap = snapshot_from_hourly(symbol, hourly.iloc[: i + 1])
        d = strategist.decide(snap)
        if d.plan is None:
            i += step
            continue
        p, sign = d.plan, 1 if d.plan.direction == "LONG" else -1
        target = p.entry + sign * target_r * p.risk_per_unit
        r, exit_i = None, min(i + max_hold, len(hourly) - 1)
        for j in range(i + 1, exit_i + 1):
            bar = hourly.iloc[j]
            hit_stop = bar.low <= p.stop_loss if sign > 0 else bar.high >= p.stop_loss
            hit_tp = bar.high >= target if sign > 0 else bar.low <= target
            if hit_stop:
                r, exit_i = -1.0, j
                break
            if hit_tp:
                r, exit_i = target_r, j
                break
        if r is None:
            r = sign * (hourly.close.iloc[exit_i] - p.entry) / p.risk_per_unit
        rows.append({"time": hourly.index[i], "direction": p.direction, "entry": p.entry,
                     "stop": p.stop_loss, "target": target, "r": r, "quality": d.setup_quality,
                     "bars_held": exit_i - i})
        i = exit_i + 1  # one position at a time
    return BacktestResult(pd.DataFrame(rows))
