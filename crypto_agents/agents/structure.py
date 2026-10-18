import numpy as np

from ..data import MarketSnapshot
from ..indicators import atr, bollinger, obv, swing_levels, vwap
from .base import Agent, AgentReport, clamp


class StructureAgent(Agent):
    """Agent 3 — price action & volume: support/resistance, VWAP, OBV, volume, Bollinger squeeze."""

    name = "Price Action & Volume Analyst"
    role = "Maps support/resistance and checks that volume confirms the move."

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        tf = snap.entry_timeframe
        df = snap.candles[tf]
        if len(df) < 60:
            return AgentReport(self.name, 0, 0, "Not enough data")
        price = df["close"].iloc[-1]
        a = atr(df).iloc[-1]
        reasons, s = [], 0.0

        # Support / resistance from swing pivots on the entry timeframe and the one above it.
        sup, res = swing_levels(df)
        tfs = list(snap.candles)
        if len(tfs) >= 2:
            s2, r2 = swing_levels(snap.candles[tfs[-2]])
            sup, res = sorted(sup + s2), sorted(res + r2)
        supports = [x for x in sup if x < price]
        resistances = [x for x in res if x > price]
        near_sup = max(supports) if supports else price - 3 * a
        near_res = min(resistances) if resistances else price + 3 * a
        d_sup, d_res = (price - near_sup) / a, (near_res - price) / a
        reasons.append(f"Nearest support {near_sup:,.2f} ({d_sup:.1f} ATR away), "
                       f"resistance {near_res:,.2f} ({d_res:.1f} ATR away)")
        if d_res < 0.75:
            s -= 0.25
            reasons.append("Price is pressing into resistance — poor place to open a long")
        if d_sup < 0.75:
            s += 0.25
            reasons.append("Price is sitting on support — poor place to open a short")

        # Breakout / breakdown of the recent range with volume.
        rng_hi = df["high"].iloc[-25:-1].max()
        rng_lo = df["low"].iloc[-25:-1].min()
        vol_ratio = df["volume"].iloc[-1] / df["volume"].iloc[-21:-1].mean()
        if price > rng_hi:
            s += 0.35 if vol_ratio > 1.3 else 0.15
            reasons.append(f"Breakout above 24-candle range high {rng_hi:,.2f} (volume x{vol_ratio:.1f})")
        elif price < rng_lo:
            s -= 0.35 if vol_ratio > 1.3 else 0.15
            reasons.append(f"Breakdown below 24-candle range low {rng_lo:,.2f} (volume x{vol_ratio:.1f})")

        # VWAP: institutions' average price over the last day.
        vw = vwap(df).iloc[-1]
        s += 0.2 if price > vw else -0.2
        reasons.append(f"Price {'above' if price > vw else 'below'} 24-candle VWAP {vw:,.2f}")

        # OBV slope vs price slope: is volume backing the move?
        o = obv(df)
        o_slope = np.sign(o.iloc[-1] - o.iloc[-20])
        p_slope = np.sign(price - df["close"].iloc[-20])
        if o_slope == p_slope:
            s += 0.2 * p_slope
            reasons.append("OBV confirms the price direction")
        else:
            s -= 0.15 * p_slope
            reasons.append("OBV disagrees with price — move lacks volume support")

        lo, mid, hi = bollinger(df["close"])
        width = (hi - lo) / mid
        squeeze = width.iloc[-1] < width.tail(120).quantile(0.2)
        if squeeze:
            reasons.append("Bollinger squeeze — volatility is compressed, expect a big move soon")

        score = clamp(s)
        confidence = clamp(0.35 + 0.4 * abs(score) + (0.15 if vol_ratio > 1.3 else 0), 0.05, 1)
        summary = f"Structure {'bullish' if score > 0.15 else 'bearish' if score < -0.15 else 'neutral'}; " \
                  f"S {near_sup:,.2f} / R {near_res:,.2f}"
        return AgentReport(self.name, score, confidence, summary, reasons, {
            "support": near_sup, "resistance": near_res,
            "supports": supports[-3:], "resistances": resistances[:3], "squeeze": bool(squeeze),
        })
