# Crypto Trading Agents

A team of analysis agents that reads **live** Binance data on any timeframe from 1 minute to 1 day.
A **Chief Strategist** turns their votes into **LONG**, **SHORT** or **NO TRADE**, with an entry,
stop-loss, take-profits, position size and a strategy playbook. Optional Claude AI agents read chart
screenshots and give a senior-trader second opinion that includes a live news check.

> ⚠️ **No system can give 100% winning signals, and this one doesn't claim to.** Markets react to news,
> liquidations and large orders that no indicator can see in advance. Instead of a made-up confidence
> number, this app **measures** how its own signals performed on the same coin and timeframe in recent
> history, and shows the range of uncertainty. Test it with paper trading first. This is not financial advice.

## Pro trade plan: where to enter (top of the Live tab)

Before every trade, the site runs the checklist a professional trader runs, and ends with one instruction:
**ENTER LONG/SHORT NOW**, **WAIT FOR TRIGGER** (with the exact level), **WAIT FOR RETEST** (don't chase) or **NO TRADE**
(with the reason). It is built from three open-source Claude skill packs, ported to 24/7 crypto, long and short:

| # | Step | What it checks | Ported from |
|---|---|---|---|
| 1 | Market regime | 0–100 score: BTC trend structure (50/200-day stack + slope), the coin's own trend structure, perpetual funding, BTC drawdown & volatility. Trading against the regime halves the size. | `crypto-regime-analyzer` (tradermonty) |
| 2 | Multi-timeframe analysis | The five agents and the Chief Strategist on three timeframes | `technical-analyst` + this app's agents |
| 3 | Setup scanner | 20-candle closing-high breakout / low breakdown, bull & bear flags, reclaimed / lost the 20 average, oversold & overbought | `trader-scanner` (day-trader-skill) |
| 4 | Entry timer | Opening-range breakout of the UTC day (1m–15m) and close beyond the 20-candle high/low. Only a **closed** candle beyond the level counts; a wick is not an entry. Says waiting (and how far), triggered (when, at what price), or expired. | `trader-entry` |
| 5 | Exit plan | Stop set **before** the entry (range midpoint, behind the 10-candle swing, or 1.5 ATR), 1R / 2R / 3R targets. Refuses a stop under 0.05% (or 3× the spread) or over 8%. | `trader-exit`, `breakout-trade-planner` |
| 6 | Time Machine | Replays the plan **10,000 times** from the coin's own candles (same time of day when there are 20+ days of history, seed 19), stop checked first, and re-runs the same rule on every past occasion it fired. Verdict against break-even, 1 in (1 + R): "close to a coin flip", "leans toward the target", "strongly toward the stop"… Fees included. | `trader-timemachine` |
| 7 | Position size | Units = risk budget ÷ (risk per unit + fees), capped by your max leverage | `trader-budget`, `position-sizer` |
| 8 | Risk manager | Stop set, loss ≤ max loss, reward:risk ≥ 1.5, stop width, daily loss (3× the per-trade risk), trades per day, no duplicate position, volatility not extreme | `trader-risk` |
| 9 | Drawdown circuit breaker | Reads your demo account: daily 2% / weekly 5% / monthly 8% loss halts, and a cool-down after a losing streak (3 losses → 2 h intraday, 2 losses → 24 h on 1h+) | `drawdown-circuit-breaker` |
| 10 | Pre-trade discipline gate | Written plan, stop before entry, size within plan, no revenge trade right after a loss (30 min intraday, 24 h on 1h+), breaker allows trading | `pre-trade-discipline-gate` |
| 11 | Next-candle check | The agent council's next-candle call agrees or disagrees | this app |

Then it tells you **how to enter**: the alert level, "wait for a 5m candle to CLOSE above X", the worst price you
should accept (half the risk past the level), the stop, where to take half off and move the stop to break-even,
the size and the most you can lose. A fan chart shows where the 10,000 replays ended. Tick **Alert me when it's time
to enter** to get a sound and a browser notification when the plan turns to ENTER NOW, and **Load plan into demo trade**
fills the demo order form (a limit order for a retest).

The Time Machine port was checked against the day-trader-skill's own published example (real TSLA 5-minute bars,
19 Oct 2026, entry 364.18 / stop 358.32 / target 370.04): the skill reports target first 29.4%, stop first 25.5%, median
364.36 and "close to a coin flip"; this port gets 29.4%, 24.8%, 364.43 and the same verdict.

The stock-only skills in those packs (13F copycat, Congress trades, SEC earnings, tax lots, rebalancing, dividend and
CANSLIM screeners) need US-equity data and aren't part of this crypto site.

```bash
python -m crypto_agents plan BTCUSDT --tf 15m                 # the whole checklist in the terminal
python -m crypto_agents plan SOLUSDT --tf 5m --side SHORT --target-r 3 --account 5000 --risk 0.5
```

## How the agents work together on the next candle (the main screen)

Pick a coin and a timeframe (e.g. **BTCUSDT · 1m**). At every candle close:

1. **Each agent reads the market**: Trend, Momentum, Price Action & Volume, Order Flow and Sentiment,
   plus a **Pattern Matching** agent that finds the 40 most similar past setups on this coin.
2. **Each agent votes on the next candle (▲ UP / ▼ DOWN).** The vote is what that agent's reading has actually
   meant for the next candle on this coin and timeframe, learned from its last ~1000 candles.
   This matters: on real 1-minute data the agents' plain "bullish/bearish" readings were **wrong more often
   than right** for the next candle (momentum 38%, the 5-agent consensus 43%), because 1m moves tend to snap back.
   Read as learned votes, the same signals point the right way.
3. **Each agent has a track record**: how often its vote was right on recent candles it never saw.
4. **The Chief weighs the votes by those track records** and gives the final call: **LONG / SHORT / NO TRADE**, with a %
   chance and a strength label (STRONG / MODERATE / WEAK). It says NO TRADE when the edge isn't proven.
5. Below the call: a **market analysis** (market overview, current position, the last 5 candles, strategies).

### Tested on real market data

Walk-forward replays where every prediction uses only earlier candles:

| Real data | Chief's LONG/SHORT calls | Notes |
|---|---|---|
| Binance 1-minute candles (small-cap coin, 2017) | **65% right** (59–71%) on 242 calls; $100,000 → ~$107,700 after 0.08% fees | Balanced: 42% LONG / 58% SHORT |
| Bitstamp BTC/USD hourly (2017) | mostly **NO TRADE** (traded 4% of hours) | Nothing reliably predicts the next BTC hour; it says so instead of guessing |

Test it yourself on any coin and timeframe:
```bash
python -m crypto_agents evaluate --symbol BTCUSDT --tf 1m            # last 1000 live candles from Binance
python -m crypto_agents evaluate --csv BTCUSDT_5m.csv --tf 5m --n 500 # a TradingView export
```
Today's big coins (BTC, ETH) are more efficient than the 2017 test coin, so expect less.

## Demo trading ($100,000 paper account)

Right under the Chief's call:
- **Market** and **limit** orders, **LONG or SHORT**, leverage **1x–20x**, stop-loss and take-profit
- **Close at candle close** for next-candle trades
- **Fill from Chief's call**: fills the side, stop and target. The levels are applied to the price you actually get.
- **Auto-trade the Chief's LONG/SHORT calls**: one trade per call, closed at that candle's close
- Live P&L from Binance prices, 0.04% fees per side, liquidation if a leveraged loss eats the margin
- **Closed trades** list each trade as **WIN / LOSS** with its P&L and why it closed (take-profit, stop-loss, candle close,
  liquidation, closed by you). Equity, total P&L and win rate are shown at the top.
- Saved in your browser. "Reset account" starts again at $100,000. No real money is involved.

CLI: `python -m crypto_agents next BTCUSDT --tf 1m --watch` prints a new prediction at every candle close.

## Features

| Feature | Where |
|---|---|
| **Pro trade plan**: 11-step pre-trade checklist, exact entry / stop / targets / size, 10,000-replay Time Machine, alert when it's time to enter | Live tab (top), `/api/plan` |
| Live TradingView chart (RSI + MACD) | Live tab |
| Live order flow, updated **every second**: taker buy/sell pressure (10 s / 60 s), order-book imbalance, a 60-second pressure strip and a candle-close countdown | Live tab (Binance WebSocket, straight from your browser) |
| **Next-candle prediction**: LONG/SHORT + % chance + STRONG/MODERATE/WEAK, candlestick patterns, pattern matching, auto-refresh at each candle close, live track record | Live tab (top), `/api/next` |
| Multi-agent analysis on 1m / 5m / 15m / 1h / 4h / 1d. Re-runs every 5/10/30/60 s or on every candle close. | Live tab, `/api/analyze` |
| Strategy selection by market regime: trend continuation, breakout, range / mean reversion, developing trend | every decision |
| **Measured** win/loss odds: chance that price is up or down after the signal window, plus the win rate of past signals with a 95% confidence range | Live tab, `/api/odds` |
| Market scanner: top 10–40 coins by 24h volume with each coin's next-candle call, STRONG/MODERATE first (live data fetched by your browser) | Scanner tab |
| Screenshot analysis: drop, paste or upload any chart. The AI reads it, predicts up or down for your time window, and the app cross-checks the reading against live data. | Screenshot AI tab, `/api/screenshot` |
| AI Senior Trader: reviews all the agents, searches the web for fresh news, and gives a verdict | "AI senior trader review" button, `/api/ai-review` |

## The agents

| # | Agent | What it checks | Data |
|---|-------|----------------|------|
| 1 | **Trend Analyst** | EMA 20/50/200 stack, ADX, +DI/-DI on 3 timeframes (higher ones count more) | candles |
| 2 | **Momentum Analyst** | RSI zones, MACD crosses, Stochastic RSI, RSI divergences | candles |
| 3 | **Price Action & Volume Analyst** | Support/resistance pivots, range breakouts with volume, VWAP, OBV, Bollinger squeeze | candles |
| 4 | **Order Flow Analyst** | Taker buy/sell ratio of the last ~1000 trades, order-book depth within ±1% and ±0.2%, whale trades, spread | order book + trades |
| 5 | **Sentiment & Derivatives Analyst** | Funding rate, open-interest change, long/short ratio, Fear & Greed, total market-cap change, BTC dominance | futures + alternative.me + CoinGecko |
| 6 | **Risk Manager** | Volatility regime, stop placement behind S/R, TP at 1.5R/2.5R/4R, position size. Can **veto** a trade. | candles |
| ★ | **Chief Strategist** | Weighted vote (order flow counts more on 1m–15m, trend counts more on 1h+), strategy choice, signal expiry | all of the above |
| AI | **Chart Vision Agent** (Claude) | Reads screenshots: trend, patterns, levels, indicators, up/down probability, trade plan | your image |
| AI | **Senior Trader Agent** (Claude) | Reviews the agents, runs a live web news search, gives a verdict | agents + web |

A trade is only signalled when the combined score is strong enough, at least 3 analysts agree,
the trade doesn't fight the higher-timeframe trend, and the Risk Manager hasn't vetoed it.
Otherwise the answer is **NO TRADE**.

### How the win/loss odds are measured
For the coin and timeframe you're looking at, the app replays the agents over the last ~120 closed candles,
using only data that was available at each moment. It then checks what actually happened next:
- **Chance up/down**: how often price was higher at the end of the signal window when the agents' score was similar to now.
- **Win rate**: how often a past signal hit TP1 (1.5R) before its stop-loss, shown with a 95% range.
  Small samples give wide ranges, and they should.

Past order-book and sentiment data isn't available, so the replay uses the candle-based agents only.

## APIs used

| API | Key needed? | Used for |
|---|---|---|
| Binance spot REST + WebSocket | no | candles, order book, trades, 24h tickers, live stream |
| Binance futures | no | funding, open interest, long/short ratio |
| alternative.me | no | Fear & Greed index |
| CoinGecko | no | total market cap change, BTC dominance |
| TradingView widget | no | live chart |
| **Anthropic Claude** | **yes**, `ANTHROPIC_API_KEY` | screenshot analysis, senior-trader review, web news search |

Get a Claude key at https://console.anthropic.com. The default model is `claude-opus-5-5`; set `CLAUDE_MODEL` to change it.
Each screenshot or review costs a few cents. Everything else works without a key.

## Run locally

```bash
pip install -r requirements-dev.txt
export ANTHROPIC_API_KEY=sk-ant-...   # optional, enables the AI features
python app.py                          # open http://localhost:5000
```

## Deploy to Vercel

1. Import the repo in Vercel. `app.py` is detected automatically.
2. **Settings → Environment Variables:** add `ANTHROPIC_API_KEY` (optional, for AI features).
3. Keep `vercel.json`'s `"regions": ["fra1"]`. Binance blocks US servers, and Vercel's default region is in the US.

The live WebSocket runs in your browser, so it uses your own connection, not Vercel's.

## Command line

```bash
python -m crypto_agents plan BTCUSDT --tf 15m                 # pro trader checklist + where to enter
python -m crypto_agents analyze BTCUSDT --tf 5m               # full analysis + measured odds
python -m crypto_agents analyze SOLUSDT --tf 15m --account 5000 --risk 0.5
python -m crypto_agents scan --tf 1h --top 30                  # rank the most traded coins
python -m crypto_agents backtest --symbol BTCUSDT              # longer hourly backtest
python -m crypto_agents backtest --csv BTCUSDT_1h.csv          # TradingView export (time,open,high,low,close,volume)
python -m crypto_agents analyze BTCUSDT --tf 5m --demo         # offline demo with synthetic data
```

## Tests

```bash
python -m pytest -q
```

## Project layout

```
app.py                 web app + JSON API (Vercel entrypoint)
vercel.json            pins the deployment to a non-US region
crypto_agents/
  data.py              live data: Binance, futures, Fear & Greed, CoinGecko; caching; demo data
  indicators.py        RSI, MACD, Stoch RSI, ADX, ATR, Bollinger, VWAP, OBV, swing levels
  agents/              trend, momentum, structure, orderflow, sentiment, risk
  strategist.py        combines the agents, picks a strategy, sets signal expiry
  odds.py              measured win/loss odds (look-ahead-free replay)
  forecast.py          next-candle prediction: agent council, Chief verdict, patterns, pattern matching, edge test
  protrader.py         pro trade plan: regime, setups, entry timer, exit plan, Time Machine, sizing, risk, breaker, gate
  analysis.py          market overview, current position, candle analysis, strategies
  evaluate.py          walk-forward test of the Chief's calls on real candles
  ai.py                Claude chart-vision and senior-trader agents
  backtest.py          longer walk-forward backtest (CLI)
  report.py            console output
  web_page.py          browser UI
```
