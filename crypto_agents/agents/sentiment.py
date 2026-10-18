from ..data import MarketSnapshot
from .base import Agent, AgentReport, clamp


class SentimentAgent(Agent):
    """Agent 4 — derivatives & crowd sentiment: funding, open interest, long/short ratio, Fear & Greed.

    Mostly contrarian: when the crowd is too one-sided, the market tends to squeeze them.
    """

    name = "Sentiment & Derivatives Analyst"
    role = "Checks how crowded longs/shorts are and how fearful or greedy the market is."

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        s, reasons, inputs = 0.0, [], 0
        price_up = snap.candles[snap.entry_timeframe]["close"].pct_change(24).iloc[-1] > 0

        if snap.funding_rate is not None:
            inputs += 1
            f = snap.funding_rate * 100
            if f > 0.05:
                s -= 0.35
                reasons.append(f"Funding {f:.3f}% is very high — longs overcrowded, long-squeeze risk")
            elif f < -0.02:
                s += 0.35
                reasons.append(f"Funding {f:.3f}% is negative — shorts crowded, short-squeeze fuel")
            else:
                reasons.append(f"Funding {f:.3f}% is normal")

        if snap.open_interest_change is not None:
            inputs += 1
            oi = snap.open_interest_change
            if oi > 3:
                s += 0.25 if price_up else -0.25
                reasons.append(f"Open interest +{oi:.1f}% with price {'rising' if price_up else 'falling'} — "
                               f"new money backs the {'up' if price_up else 'down'} move")
            elif oi < -3:
                reasons.append(f"Open interest {oi:.1f}% — positions closing, move may be losing fuel")
            else:
                reasons.append(f"Open interest flat ({oi:+.1f}%)")

        if snap.long_short_ratio is not None:
            inputs += 1
            ls = snap.long_short_ratio
            if ls > 2.5:
                s -= 0.2
                reasons.append(f"Long/short ratio {ls:.2f} — retail heavily long (contrarian bearish)")
            elif ls < 0.8:
                s += 0.2
                reasons.append(f"Long/short ratio {ls:.2f} — retail heavily short (contrarian bullish)")
            else:
                reasons.append(f"Long/short ratio {ls:.2f} — balanced")

        if snap.fear_greed is not None:
            inputs += 1
            fg = snap.fear_greed
            if fg >= 80:
                s -= 0.3
                reasons.append(f"Fear & Greed {fg} = extreme greed (tops form here)")
            elif fg <= 20:
                s += 0.3
                reasons.append(f"Fear & Greed {fg} = extreme fear (bottoms form here)")
            else:
                reasons.append(f"Fear & Greed {fg} — no extreme")

        if snap.market is not None:
            inputs += 1
            mc, dom = snap.market["market_cap_change_24h"], snap.market["btc_dominance"]
            if mc > 3:
                s += 0.15
                reasons.append(f"Total crypto market cap {mc:+.1f}% in 24h — risk-on market")
            elif mc < -3:
                s -= 0.15
                reasons.append(f"Total crypto market cap {mc:+.1f}% in 24h — risk-off market")
            else:
                reasons.append(f"Total crypto market cap {mc:+.1f}% in 24h")
            reasons.append(f"BTC dominance {dom:.1f}%")

        if not inputs:
            return AgentReport(self.name, 0, 0, "No sentiment/derivatives data available — abstaining")
        score = clamp(s)
        confidence = clamp(0.15 * inputs + 0.3 * abs(score), 0, 0.9)
        summary = "Crowd positioning " + ("favours longs (contrarian)" if score > 0.15 else
                                          "favours shorts (contrarian)" if score < -0.15 else "is not extreme")
        return AgentReport(self.name, score, confidence, summary, reasons)
