"""Plain-English market report: market overview, current position, candle-by-candle analysis and strategies."""
from __future__ import annotations

import numpy as np

from .data import TF_SECONDS, MarketSnapshot
from .forecast import BEARISH, BULLISH, NEUTRAL, detect_patterns
from .indicators import atr, ema, rsi, vwap


def _pct(a: float, b: float) -> float:
    return (a / b - 1) * 100 if b else 0.0


def _fmt(x: float) -> str:
    return f"{x:,.2f}" if abs(x) >= 1 else f"{x:.6g}"


def market_report(snap: MarketSnapshot, decision, forecast: dict | None = None) -> dict:
    tf = snap.entry_timeframe
    df = snap.candles[tf]
    price = float(df["close"].iloc[-1])
    reports = {r.agent: r for r in decision.reports}
    trend = reports.get("Trend Analyst")
    structure = reports.get("Price Action & Volume Analyst")
    risk = reports.get("Risk Manager")
    sections = []

    # ---- market overview
    items = []
    for t, d in snap.candles.items():
        if len(d) > 25:
            items.append(f"{t}: {_pct(d['close'].iloc[-1], d['close'].iloc[-25]):+.2f}% over the last 24 candles"
                         + (f", trend {trend.data['per_timeframe'][t]}" if trend and t in trend.data.get("per_timeframe", {}) else ""))
    if risk:
        regime = risk.data.get("volatility_regime", 1)
        items.append(f"Volatility: {risk.reasons[0].split(',')[0]} — "
                     + ("very high, expect big swings" if regime > 1.8 else "above normal" if regime > 1.2
                        else "quiet, moves are small" if regime < 0.7 else "normal"))
    sent = reports.get("Sentiment & Derivatives Analyst")
    if sent and sent.confidence > 0:
        items.append(f"Sentiment: {sent.summary}")
        items += [r for r in sent.reasons if "Fear & Greed" in r or "Funding" in r][:2]
    if snap.market:
        items.append(f"Whole crypto market {snap.market['market_cap_change_24h']:+.1f}% in 24h, BTC dominance {snap.market['btc_dominance']:.1f}%")
    sections.append({"title": "Market overview", "items": items})

    # ---- current position of price
    items = []
    look = df.tail(50)
    hi, lo = float(look["high"].max()), float(look["low"].min())
    pos = (price - lo) / (hi - lo) if hi > lo else 0.5
    where = "at the top" if pos > 0.85 else "in the upper half" if pos > 0.55 else "in the middle" if pos > 0.45 \
        else "in the lower half" if pos > 0.15 else "at the bottom"
    items.append(f"Price {_fmt(price)} is {where} of its last 50-candle range ({_fmt(lo)} – {_fmt(hi)}), {pos:.0%} of the way up")
    if structure:
        s, r = structure.data.get("support"), structure.data.get("resistance")
        if s and r:
            items.append(f"Nearest support {_fmt(s)} ({_pct(s, price):+.2f}%), nearest resistance {_fmt(r)} ({_pct(r, price):+.2f}%)")
    vw = float(vwap(df).iloc[-1])
    items.append(f"{'Above' if price > vw else 'Below'} VWAP {_fmt(vw)} — {'buyers' if price > vw else 'sellers'} have the upper hand today")
    emas = {n: float(ema(df['close'], n).iloc[-1]) for n in (20, 50, 200)}
    above = [f"EMA{n}" for n, v in emas.items() if price > v]
    items.append(f"Above {', '.join(above)}" if above else "Below EMA20, EMA50 and EMA200 — bearish structure")
    r14 = float(rsi(df["close"]).iloc[-1])
    items.append(f"RSI {r14:.0f} — " + ("overbought" if r14 >= 70 else "oversold" if r14 <= 30 else "neutral zone"))
    sections.append({"title": "Current position", "items": items})

    # ---- candle analysis (closed candles + the live one)
    step = TF_SECONDS[tf]
    import time
    forming = df.index[-1].timestamp() + step > time.time()
    closed = df.iloc[:-1] if forming else df
    pats = detect_patterns(closed).tail(5)
    avg_body = float((closed["close"] - closed["open"]).abs().tail(50).mean()) or 1e-12
    a = float(atr(closed).iloc[-1]) or 1e-12
    candles = []
    for ts, row in closed.tail(5).iterrows():
        body = row.close - row.open
        rng = row.high - row.low or 1e-12
        names = [n for k, n in {**BULLISH, **BEARISH, **NEUTRAL}.items() if pats.loc[ts, k]]
        wick = ("long upper wick (selling pressure)" if (row.high - max(row.open, row.close)) / rng > 0.5 else
                "long lower wick (buying pressure)" if (min(row.open, row.close) - row.low) / rng > 0.5 else "")
        size = abs(body) / avg_body
        candles.append({
            "time": int(ts.timestamp()), "color": "green" if body > 0 else "red" if body < 0 else "flat",
            "change_pct": _pct(row.close, row.open), "range_atr": rng / a,
            "note": ", ".join(x for x in [("big" if size > 1.8 else "small" if size < 0.5 else "normal") + " body", wick, *names] if x),
        })
    greens = sum(c["color"] == "green" for c in candles)
    summary = [f"Last 5 closed candles: {greens} green, {5 - greens} red"]
    if forming:
        live = df.iloc[-1]
        summary.append(f"Current candle so far: {_pct(live.close, live.open):+.3f}% "
                       f"({(time.time() - df.index[-1].timestamp()) / step:.0%} of the candle done)")
    sections.append({"title": "Candle analysis", "items": summary})

    # ---- strategies
    items = []
    if forecast and not forecast.get("error"):
        fc = forecast
        p = fc["plan"]
        items.append(f"Next-candle scalp ({tf}): Chief says {fc['final_call']} — "
                     + (f"enter {fc['final_call'].lower()} near {_fmt(p['entry'])}, stop {_fmt(p['stop_loss'])}, "
                        f"target {_fmt(p['take_profit'])}, exit at the candle close"
                        if fc["final_call"] != "NO TRADE" else "skip this candle and wait for a STRONG or MODERATE call"))
    items.append(f"Bigger picture ({decision.horizon_text}): {decision.action} — strategy: {decision.strategy}. {decision.playbook}")
    if decision.plan:
        pl = decision.plan
        items.append(f"Swing plan: entry {_fmt(pl.entry)}, stop {_fmt(pl.stop_loss)}, targets "
                     + ", ".join(_fmt(t) for t in pl.take_profits) + f"; risk {pl.risk_amount:,.2f} USDT")
    items.append("Risk rule: never risk more than 1–2% of your account on one trade, and always set the stop-loss first")
    sections.append({"title": "Strategies", "items": items})
    return {"sections": sections, "candles": candles}
