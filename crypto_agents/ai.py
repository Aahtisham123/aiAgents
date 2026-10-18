"""Claude-powered agents (optional — needs ANTHROPIC_API_KEY):

- Chart Vision Agent: reads a chart screenshot (TradingView, exchange app, ...) and returns a structured read.
- Senior Trader Agent: reviews the five analysts' live output, searches the web for fresh news about
  the coin, and gives a second opinion.
"""
from __future__ import annotations

import json
import os
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(timeout=120.0)


class ChartRead(BaseModel):
    symbol_guess: str = Field(description="Trading pair shown, as Binance symbol e.g. BTCUSDT; empty if unreadable")
    timeframe_guess: str = Field(description="Chart timeframe if visible: 1m, 5m, 15m, 1h, 4h or 1d; empty if unknown")
    price_on_chart: float | None = Field(description="Last price visible on the chart, if readable")
    trend: Literal["UP", "DOWN", "SIDEWAYS", "UNCLEAR"]
    market_structure: str = Field(description="Higher highs/lows, lower highs/lows, range, etc.")
    patterns: list[str] = Field(description="Chart and candlestick patterns visible")
    indicators_seen: list[str] = Field(description="Indicators visible and what they show")
    supports: list[float]
    resistances: list[float]
    bias_next_period: Literal["UP", "DOWN", "SIDEWAYS", "UNCLEAR"]
    probability_up_pct: int = Field(description="Your honest estimate 0-100 that price is higher after the stated horizon")
    suggested_action: Literal["LONG", "SHORT", "WAIT"]
    entry: float | None
    stop_loss: float | None
    take_profits: list[float]
    invalidation: str = Field(description="What price action would prove this read wrong")
    reasoning: str = Field(description="Step-by-step explanation in plain English")
    risks: list[str]
    image_quality_issues: str = Field(description="Anything unreadable or cut off; empty if fine")


VISION_SYSTEM = """You are an experienced crypto technical analyst reading a chart screenshot.
Read only what is actually visible: price axis, candles, drawn levels, indicators, timeframe label.
Never invent numbers you cannot read; leave them null and say so in image_quality_issues.
Give an honest probability: charts alone rarely justify more than 60-65% confidence in either direction.
If the picture is not a price chart, say so in image_quality_issues and answer WAIT/UNCLEAR."""


def analyze_screenshot(image_b64: str, media_type: str, timeframe: str = "", horizon: str = "",
                       note: str = "") -> ChartRead:
    ask = "Analyze this chart screenshot and say whether price is more likely to go up or down"
    if horizon:
        ask += f" over the next {horizon}"
    if timeframe:
        ask += f". The trader says the chart timeframe is {timeframe}"
    if note:
        ask += f". Trader's note: {note}"
    response = _client().beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": "high"},
        system=VISION_SYSTEM,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}},
            {"type": "text", "text": ask + "."},
        ]}],
        output_format=ChartRead,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError("The AI could not analyze this image.")
    return response.parsed_output


REVIEW_SYSTEM = """You are the Senior Trader supervising a team of rule-based trading agents.
You receive their live analysis as JSON. Your job:
1. Use web search to check for news from the last 24-48 hours that could move this coin
   (hacks, listings/delistings, ETF/regulatory news, token unlocks, macro events like CPI/FOMC).
2. Look for contradictions or weak points in the agents' reasoning.
3. Give a verdict.

Reply in Markdown with exactly these sections:
**Verdict:** AGREE / CAUTION / DISAGREE — one sentence why.
**News check:** bullet points with dates (or "nothing significant found").
**What the agents may be missing:** bullets.
**What would change the call:** bullets with price levels.
Be concise and honest. Never promise profits; never claim certainty."""


def review_decision(decision: dict, odds: dict | None = None) -> str:
    payload = {"decision": decision, "historical_odds": odds}
    messages = [{"role": "user", "content": "Live agent analysis:\n```json\n"
                 + json.dumps(payload, default=str)[:60000] + "\n```"}]
    client = _client()
    text = ""
    for _ in range(4):  # server-side web search may pause a long turn; resume it
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=[FALLBACK_BETA],
            fallbacks="default",
            output_config={"effort": "medium"},
            system=REVIEW_SYSTEM,
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 4}],
            messages=messages,
        )
        text += "".join(b.text for b in response.content if b.type == "text")
        if response.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": response.content})
    if response.stop_reason == "refusal":
        raise RuntimeError("The AI declined to review this request.")
    return text.strip()
