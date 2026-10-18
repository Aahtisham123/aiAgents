from ..data import MarketSnapshot
from ..indicators import adx, ema
from .base import Agent, AgentReport, clamp

TF_WEIGHTS = {"1w": 0.35, "1d": 0.5, "4h": 0.3, "1h": 0.2, "15m": 0.1, "5m": 0.05}


class TrendAgent(Agent):
    """Agent 1 — multi-timeframe trend: EMA 20/50/200 stack and ADX trend strength."""

    name = "Trend Analyst"
    role = "Reads the trend on every timeframe, higher timeframes first."

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        total, weight_sum, reasons, per_tf = 0.0, 0.0, [], {}
        strengths = []
        for tf, df in snap.candles.items():
            if len(df) < 60:
                continue
            c = df["close"]
            e20, e50 = ema(c, 20).iloc[-1], ema(c, 50).iloc[-1]
            e200 = ema(c, 200).iloc[-1] if len(df) >= 200 else ema(c, len(df) // 2).iloc[-1]
            a, pdi, mdi = (s.iloc[-1] for s in adx(df))
            price = c.iloc[-1]

            s = 0.0
            s += 0.4 if price > e200 else -0.4
            s += 0.3 if e20 > e50 else -0.3
            s += 0.3 if pdi > mdi else -0.3
            strength = min(a / 40, 1.0)  # ADX 40+ = very strong trend
            s *= 0.5 + 0.5 * strength
            strengths.append(strength)

            w = TF_WEIGHTS.get(tf, 0.2)
            total += s * w
            weight_sum += w
            label = "UP" if s > 0.15 else "DOWN" if s < -0.15 else "SIDEWAYS"
            per_tf[tf] = label
            reasons.append(
                f"{tf}: {label} — price {'above' if price > e200 else 'below'} EMA200, "
                f"EMA20 {'>' if e20 > e50 else '<'} EMA50, ADX {a:.0f} ({'+DI' if pdi > mdi else '-DI'} leads)"
            )

        if not weight_sum:
            return AgentReport(self.name, 0, 0, "Not enough data", [])
        score = clamp(total / weight_sum)
        labels = list(per_tf.values())
        aligned = len(set(labels)) == 1 and labels[0] != "SIDEWAYS"
        confidence = clamp((0.6 if aligned else 0.3) + 0.4 * sum(strengths) / len(strengths), 0, 1)
        summary = ("All timeframes aligned " + labels[0]) if aligned else "Timeframes disagree: " + ", ".join(
            f"{tf} {v}" for tf, v in per_tf.items()
        )
        return AgentReport(self.name, score, confidence, summary, reasons, {"per_timeframe": per_tf})
