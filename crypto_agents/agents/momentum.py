import numpy as np

from ..data import MarketSnapshot
from ..indicators import macd, rsi, stoch_rsi
from .base import Agent, AgentReport, clamp


def _divergence(close, osc, lookback: int = 40) -> int:
    """+1 bullish divergence (lower low in price, higher low in RSI), -1 bearish, 0 none."""
    c, o = close.tail(lookback).values, osc.tail(lookback).values
    half = lookback // 2
    a, b = slice(0, half), slice(half, lookback)
    if c[b].min() < c[a].min() and o[b][np.argmin(c[b])] > o[a][np.argmin(c[a])] and o[b].min() < 40:
        return 1
    if c[b].max() > c[a].max() and o[b][np.argmax(c[b])] < o[a][np.argmax(c[a])] and o[b].max() > 60:
        return -1
    return 0


class MomentumAgent(Agent):
    """Agent 2 — momentum oscillators: RSI, MACD, Stochastic RSI and divergences."""

    name = "Momentum Analyst"
    role = "Checks whether buyers or sellers have momentum, and spots exhaustion."

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        tfs = list(snap.candles)[-2:]  # the two lowest timeframes, e.g. 4h + 1h
        scores, reasons, extremes = [], [], 0
        for tf in tfs:
            close = snap.candles[tf]["close"]
            if len(close) < 60:
                continue
            r = rsi(close)
            r_now, r_prev = r.iloc[-1], r.iloc[-4]
            line, sig, hist = macd(close)
            k, d = stoch_rsi(close)
            s = 0.0

            # RSI: above 50 = bullish momentum, but stretched readings mean late entries.
            if r_now >= 75:
                s -= 0.2
                extremes += 1
                reasons.append(f"{tf}: RSI {r_now:.0f} overbought — late to buy, pullback risk")
            elif r_now <= 25:
                s += 0.2
                extremes += 1
                reasons.append(f"{tf}: RSI {r_now:.0f} oversold — late to sell, bounce risk")
            else:
                s += 0.35 * np.sign(r_now - 50) * min(abs(r_now - 50) / 20, 1)
                reasons.append(f"{tf}: RSI {r_now:.0f} ({'rising' if r_now > r_prev else 'falling'})")

            s += 0.25 if hist.iloc[-1] > 0 else -0.25
            if hist.iloc[-1] > hist.iloc[-2]:
                s += 0.1
            else:
                s -= 0.1
            crossed = np.sign(hist.iloc[-1]) != np.sign(hist.iloc[-3])
            reasons.append(
                f"{tf}: MACD histogram {'positive' if hist.iloc[-1] > 0 else 'negative'}"
                f"{' (fresh cross)' if crossed else ''}, {'expanding' if abs(hist.iloc[-1]) > abs(hist.iloc[-2]) else 'contracting'}"
            )

            if not np.isnan(k.iloc[-1]):
                if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2] and k.iloc[-1] < 30:
                    s += 0.2
                    reasons.append(f"{tf}: Stoch RSI bullish cross from oversold")
                elif k.iloc[-1] < d.iloc[-1] and k.iloc[-2] >= d.iloc[-2] and k.iloc[-1] > 70:
                    s -= 0.2
                    reasons.append(f"{tf}: Stoch RSI bearish cross from overbought")

            div = _divergence(close, r)
            if div:
                s += 0.3 * div
                reasons.append(f"{tf}: {'BULLISH' if div > 0 else 'BEARISH'} RSI divergence")
            scores.append(clamp(s))

        if not scores:
            return AgentReport(self.name, 0, 0, "Not enough data")
        score = clamp(sum(scores) / len(scores))
        agree = all(np.sign(x) == np.sign(scores[0]) for x in scores)
        confidence = clamp((0.6 if agree else 0.3) + 0.3 * abs(score) - 0.15 * extremes, 0.05, 1)
        summary = f"Momentum {'bullish' if score > 0.15 else 'bearish' if score < -0.15 else 'mixed'} " \
                  f"({'timeframes agree' if agree else 'timeframes disagree'})"
        return AgentReport(self.name, score, confidence, summary, reasons)
