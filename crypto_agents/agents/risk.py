from __future__ import annotations

from dataclasses import dataclass

from ..data import MarketSnapshot
from ..indicators import atr
from .base import Agent, AgentReport


@dataclass
class TradePlan:
    direction: str  # LONG / SHORT
    entry: float
    stop_loss: float
    take_profits: list[float]
    risk_per_unit: float
    reward_risk: float  # to the first take-profit
    position_size: float  # coin units
    position_value: float  # in quote currency (USDT)
    leverage_needed: float
    risk_amount: float


class RiskManagerAgent(Agent):
    """Agent 5 — risk manager: volatility check, stop-loss, take-profits, position size, veto power."""

    name = "Risk Manager"
    role = "Sizes the trade, sets stop-loss and targets, and vetoes bad risk/reward."

    def __init__(self, account_size: float = 1000.0, risk_pct: float = 1.0, atr_stop: float = 1.5,
                 min_rr: float = 1.5):
        self.account_size = account_size
        self.risk_pct = risk_pct
        self.atr_stop = atr_stop
        self.min_rr = min_rr

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        df = snap.candles[snap.entry_timeframe]
        a = atr(df)
        atr_pct = a.iloc[-1] / df["close"].iloc[-1] * 100
        regime = a.iloc[-1] / a.tail(200).median()
        reasons = [f"ATR {a.iloc[-1]:,.2f} ({atr_pct:.2f}% of price), {regime:.1f}x its normal level"]
        if regime > 2.2:
            reasons.append("Volatility is extreme — stops get hunted, size down or stay out")
        # The risk manager has no directional opinion: score 0, confidence used as a 'safety' rating.
        safety = max(0.0, min(1.0, 1.4 - regime / 2))
        return AgentReport(self.name, 0.0, safety, f"Volatility {regime:.1f}x normal", reasons,
                           {"atr": float(a.iloc[-1]), "volatility_regime": float(regime)})

    def build_plan(self, snap: MarketSnapshot, direction: str, structure: dict) -> tuple[TradePlan, list[str]]:
        df = snap.candles[snap.entry_timeframe]
        entry = float(df["close"].iloc[-1])
        a = float(atr(df).iloc[-1])
        sign = 1 if direction == "LONG" else -1

        # Stop: behind the nearest support/resistance if it's close, otherwise 1.5 ATR.
        level = structure.get("support") if direction == "LONG" else structure.get("resistance")
        stop = entry - sign * self.atr_stop * a
        if level is not None and abs(entry - level) < 3 * a:
            stop = min(stop, level - 0.3 * a) if direction == "LONG" else max(stop, level + 0.3 * a)
        risk = abs(entry - stop)

        targets = [entry + sign * risk * r for r in (1.5, 2.5, 4.0)]
        opposing = structure.get("resistance") if direction == "LONG" else structure.get("support")
        warnings = []
        if opposing is not None:
            room = (opposing - entry) * sign
            if 0 < room < self.min_rr * risk:
                warnings.append(f"Only {room / risk:.1f}R of room before the next "
                                f"{'resistance' if direction == 'LONG' else 'support'} at {opposing:,.2f}")

        risk_amount = self.account_size * self.risk_pct / 100
        size = risk_amount / risk if risk else 0.0
        value = size * entry
        plan = TradePlan(direction, entry, stop, targets, risk, 1.5, size, value,
                         value / self.account_size if self.account_size else 0, risk_amount)
        return plan, warnings
