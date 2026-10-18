from __future__ import annotations

from dataclasses import dataclass, field

from ..data import MarketSnapshot


@dataclass
class AgentReport:
    agent: str
    score: float  # -1 (strong bearish) .. +1 (strong bullish)
    confidence: float  # 0 .. 1, how much the agent trusts its own reading
    summary: str
    reasons: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)

    @property
    def bias(self) -> str:
        if self.score > 0.15:
            return "BULLISH"
        if self.score < -0.15:
            return "BEARISH"
        return "NEUTRAL"


class Agent:
    name = "agent"
    role = ""

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        raise NotImplementedError


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))
