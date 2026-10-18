"""The Chief Strategist: runs the five agents, weighs their votes and issues a trade decision."""
from __future__ import annotations

from dataclasses import dataclass, field

from .agents import (AgentReport, MomentumAgent, RiskManagerAgent, SentimentAgent,
                     StructureAgent, TradePlan, TrendAgent)
from .data import MarketSnapshot

# How much each analyst's vote counts. Trend is king; sentiment is a tiebreaker.
WEIGHTS = {TrendAgent.name: 0.35, MomentumAgent.name: 0.25,
           StructureAgent.name: 0.25, SentimentAgent.name: 0.15}


@dataclass
class Decision:
    symbol: str
    action: str  # LONG / SHORT / NO TRADE
    score: float  # combined -1..1
    setup_quality: int  # 0..100 — how many boxes are ticked. NOT a win probability.
    reports: list[AgentReport]
    plan: TradePlan | None = None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class Strategist:
    def __init__(self, account_size: float = 1000.0, risk_pct: float = 1.0, threshold: float = 0.3,
                 min_agreeing: int = 3):
        self.analysts = [TrendAgent(), MomentumAgent(), StructureAgent(), SentimentAgent()]
        self.risk = RiskManagerAgent(account_size, risk_pct)
        self.threshold = threshold
        self.min_agreeing = min_agreeing

    def decide(self, snap: MarketSnapshot) -> Decision:
        reports = [a.analyze(snap) for a in self.analysts]
        risk_report = self.risk.analyze(snap)
        by_name = {r.agent: r for r in reports}

        voting = [r for r in reports if r.confidence > 0]
        weight_sum = sum(WEIGHTS[r.agent] for r in voting) or 1
        score = sum(WEIGHTS[r.agent] * r.score * (0.5 + 0.5 * r.confidence) for r in voting) / weight_sum

        direction = "LONG" if score > 0 else "SHORT"
        sign = 1 if score > 0 else -1
        agreeing = [r for r in voting if r.score * sign > 0.15]
        opposing = [r for r in voting if r.score * sign < -0.15]
        quality = round(100 * min(1.0, abs(score) / 0.6) * (len(agreeing) / max(len(voting), 1))
                        * risk_report.confidence)

        reasons, warnings = [], []
        trend = by_name[TrendAgent.name]
        action = direction
        if abs(score) < self.threshold:
            action = "NO TRADE"
            reasons.append(f"Combined score {score:+.2f} is below the ±{self.threshold} threshold — no clear edge")
        elif len(agreeing) < min(self.min_agreeing, len(voting)):
            action = "NO TRADE"
            reasons.append(f"Only {len(agreeing)} of {len(voting)} analysts agree on {direction}")
        elif trend.score * sign < -0.15:
            action = "NO TRADE"
            reasons.append(f"Refusing to trade {direction} against the higher-timeframe trend")
        elif risk_report.confidence < 0.2:
            action = "NO TRADE"
            reasons.append("Risk Manager veto: volatility is extreme")

        plan = None
        if action != "NO TRADE":
            plan, plan_warnings = self.risk.build_plan(snap, action, by_name[StructureAgent.name].data)
            warnings += plan_warnings
            if plan_warnings:
                quality = round(quality * 0.7)
            reasons.append(f"{len(agreeing)} of {len(voting)} analysts agree on {action} "
                           f"(combined score {score:+.2f})")
        for r in opposing:
            warnings.append(f"{r.agent} disagrees: {r.summary}")
        warnings += [n for n in snap.notes]
        return Decision(snap.symbol, action, score, quality, reports + [risk_report], plan, reasons, warnings)
