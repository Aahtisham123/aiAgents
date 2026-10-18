from ..data import MarketSnapshot
from .base import Agent, AgentReport, clamp


class OrderFlowAgent(Agent):
    """Agent 6 — live order flow: who is hitting the market right now and where the resting liquidity sits.

    This is the fastest-changing information the system has and matters most for 1m/5m/15m trades.
    """

    name = "Order Flow Analyst"
    role = "Reads the live order book and the last ~1000 trades for real-time buying/selling pressure."

    def analyze(self, snap: MarketSnapshot) -> AgentReport:
        of = snap.orderflow
        df = snap.candles[snap.entry_timeframe]
        reasons, s = [], 0.0

        # Taker flow inside the candles (works for live data and CSV/backtests that carry it).
        if "taker_buy_volume" in df.columns:
            recent = df.tail(6)
            ratio = recent["taker_buy_volume"].sum() / max(recent["volume"].sum(), 1e-12)
            s += clamp((ratio - 0.5) * 3, -0.3, 0.3)
            reasons.append(f"Last 6 {snap.entry_timeframe} candles: {ratio:.0%} of volume was aggressive buying")

        if of is None:
            if not reasons:
                return AgentReport(self.name, 0, 0, "No live order-flow data — abstaining")
            score = clamp(s)
            return AgentReport(self.name, score, 0.3, "Candle taker-flow only", reasons)

        tb = of["taker_buy_ratio"]
        s += clamp((tb - 0.5) * 2.5, -0.4, 0.4)
        reasons.append(f"Last {of['trades']} trades (~{of['trades_window_sec']:.0f}s): "
                       f"{tb:.0%} taker buys / {1 - tb:.0%} taker sells")

        imb = of["book_imbalance_1pct"]
        s += clamp(imb * 0.6, -0.25, 0.25)
        reasons.append(f"Order book within ±1%: {of['bid_depth_1pct']:,.0f} USDT bids vs "
                       f"{of['ask_depth_1pct']:,.0f} USDT asks (imbalance {imb:+.0%})")
        near = of["book_imbalance_0_2pct"]
        if abs(near) > 0.3:
            reasons.append(f"Strong {'bid' if near > 0 else 'ask'} wall within ±0.2% of price ({near:+.0%})")

        wb, ws = of["whale_buy"], of["whale_sell"]
        if wb + ws > 0:
            w = (wb - ws) / (wb + ws)
            s += 0.15 * w
            reasons.append(f"Largest 2% of trades: {wb:,.0f} USDT bought vs {ws:,.0f} USDT sold")
        if of["spread_pct"] > 0.1:
            reasons.append(f"Wide spread {of['spread_pct']:.2f}% — thin liquidity, expect slippage")

        score = clamp(s)
        confidence = clamp(0.4 + 0.5 * abs(score), 0, 0.9)
        summary = ("Buyers are aggressive right now" if score > 0.15 else
                   "Sellers are aggressive right now" if score < -0.15 else "Order flow balanced")
        return AgentReport(self.name, score, confidence, summary, reasons, {
            "taker_buy_ratio": tb, "book_imbalance": imb})
