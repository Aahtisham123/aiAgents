"""The Chief Strategist: runs the analysts, weighs their votes, picks a strategy and issues a trade decision."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from .agents import (AgentReport, MomentumAgent, OrderFlowAgent, RiskManagerAgent, SentimentAgent,
                     StructureAgent, TradePlan, TrendAgent)
from .data import TF_SECONDS, MarketSnapshot

# How much each analyst's vote counts. Short timeframes lean on order flow; longer ones on trend.
WEIGHTS = {
    "scalp": {TrendAgent.name: 0.25, MomentumAgent.name: 0.25, StructureAgent.name: 0.2,
              OrderFlowAgent.name: 0.2, SentimentAgent.name: 0.1},
    "swing": {TrendAgent.name: 0.35, MomentumAgent.name: 0.2, StructureAgent.name: 0.2,
              OrderFlowAgent.name: 0.1, SentimentAgent.name: 0.15},
}
# How many entry candles a signal stays valid for before it is stale.
HORIZON = {"1m": 30, "5m": 24, "15m": 16, "1h": 24, "4h": 18, "1d": 10}


def _duration(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60} minutes"
    if seconds < 86400 * 2:
        return f"{seconds / 3600:g} hours"
    return f"{seconds / 86400:g} days"


@dataclass
class Decision:
    symbol: str
    timeframe: str
    action: str  # LONG / SHORT / NO TRADE
    score: float  # combined -1..1
    setup_quality: int  # 0..100 — how many boxes are ticked. NOT a win probability.
    strategy: str
    playbook: str
    horizon_candles: int
    horizon_text: str
    price: float
    reports: list[AgentReport]
    plan: TradePlan | None = None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)


class Strategist:
    def __init__(self, account_size: float = 1000.0, risk_pct: float = 1.0, threshold: float = 0.3,
                 min_agreeing: int = 3):
        self.analysts = [TrendAgent(), MomentumAgent(), StructureAgent(), OrderFlowAgent(), SentimentAgent()]
        self.risk = RiskManagerAgent(account_size, risk_pct)
        self.threshold = threshold
        self.min_agreeing = min_agreeing

    @staticmethod
    def _strategy(trend: AgentReport, structure: AgentReport) -> tuple[str, str]:
        adx = trend.data.get("entry_adx") or 0
        if structure.data.get("squeeze"):
            return ("Breakout", "Volatility is compressed. Enter on a candle close outside the range with "
                    "rising volume; skip it if the breakout candle closes back inside.")
        if adx >= 25 and abs(trend.score) > 0.4:
            return ("Trend continuation", "Strong trend. Enter with the trend, ideally on a pullback to the "
                    "20 EMA or VWAP; don't chase extended candles.")
        if adx < 20:
            return ("Range / mean reversion", "No real trend. Buy near support, sell near resistance, and "
                    "take profit early at the middle of the range. Breakouts often fail here.")
        return ("Developing trend", "Trend is forming but not confirmed. Use smaller size and wait for a "
                "candle close in the signal direction.")

    def decide(self, snap: MarketSnapshot) -> Decision:
        tf = snap.entry_timeframe
        reports = [a.analyze(snap) for a in self.analysts]
        risk_report = self.risk.analyze(snap)
        by_name = {r.agent: r for r in reports}
        weights = WEIGHTS["scalp" if tf in ("1m", "5m", "15m") else "swing"]

        voting = [r for r in reports if r.confidence > 0]
        weight_sum = sum(weights[r.agent] for r in voting) or 1
        score = sum(weights[r.agent] * r.score * (0.5 + 0.5 * r.confidence) for r in voting) / weight_sum

        direction = "LONG" if score > 0 else "SHORT"
        sign = 1 if score > 0 else -1
        agreeing = [r for r in voting if r.score * sign > 0.15]
        opposing = [r for r in voting if r.score * sign < -0.15]
        quality = round(100 * min(1.0, abs(score) / 0.6) * (len(agreeing) / max(len(voting), 1))
                        * risk_report.confidence)
        trend, structure = by_name[TrendAgent.name], by_name[StructureAgent.name]
        strategy, playbook = self._strategy(trend, structure)

        reasons, warnings = [], []
        action = direction
        ranging = strategy.startswith("Range")
        if abs(score) < self.threshold:
            action = "NO TRADE"
            reasons.append(f"Combined score {score:+.2f} is below the ±{self.threshold} threshold — no clear edge")
        elif len(agreeing) < min(self.min_agreeing, len(voting)):
            action = "NO TRADE"
            reasons.append(f"Only {len(agreeing)} of {len(voting)} analysts agree on {direction}")
        elif trend.score * sign < (-0.15 if not ranging else -0.5):
            action = "NO TRADE"
            reasons.append(f"Refusing to trade {direction} against the higher-timeframe trend")
        elif risk_report.confidence < 0.2:
            action = "NO TRADE"
            reasons.append("Risk Manager veto: volatility is extreme")

        plan = None
        if action != "NO TRADE":
            plan, plan_warnings = self.risk.build_plan(snap, action, structure.data)
            warnings += plan_warnings
            if plan_warnings:
                quality = round(quality * 0.7)
            reasons.append(f"{len(agreeing)} of {len(voting)} analysts agree on {action} "
                           f"(combined score {score:+.2f})")
        for r in opposing:
            warnings.append(f"{r.agent} disagrees: {r.summary}")
        warnings += list(snap.notes)

        horizon = HORIZON.get(tf, 20)
        return Decision(
            snap.symbol, tf, action, score, quality, strategy, playbook, horizon,
            f"{horizon} × {tf} candles (≈{_duration(horizon * TF_SECONDS[tf])})", snap.price,
            reports + [risk_report], plan, reasons, warnings,
        )
