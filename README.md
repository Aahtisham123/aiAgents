# Crypto Trading Agents

A team of analysis agents that reads **live** Binance data on any timeframe from 1 minute to 1 day.
A **Chief Strategist** turns their votes into **LONG**, **SHORT** or **NO TRADE**, with an entry,
stop-loss, take-profits, position size and a strategy playbook. Optional Claude AI agents read chart
screenshots and give a senior-trader second opinion that includes a live news check.

> ⚠️ **No system can give 100% winning signals, and this one doesn't claim to.** Markets react to news,
> liquidations and large orders that no indicator can see in advance. Instead of a made-up confidence
> number, this app **measures** how its own signals performed on the same coin and timeframe in recent
> history, and shows the range of uncertainty. Test it with paper trading first. This is not financial advice.

## Next-candle prediction (the main screen)

Open the site, type a coin (e.g. **BTCUSDT**) and pick a timeframe (e.g. **1m**). The top card tells you:

```
Next 1m candle · BTCUSDT · 21:19–21:20          closes in 0:47
▲ LONG  57% chance                              [MODERATE] Possible trade: use a small size
Why
 • Candle pattern on the last closed candle: Bullish engulfing
 • Pattern match: in the 40 most similar past setups, the next candle went up 25 times and down 15 → 61% up
 • Indicator model: 54% up — pushing up: higher-timeframe trend, taker buying
 • Live order flow agrees: buyers are aggressive right now
Entry · Stop-loss · Target · Recent accuracy
Live track record: 31 of 52 right (60%)
```

- It **always** gives a direction (LONG or SHORT) and a % chance.
- The **strength** label tells you whether to act:
  **STRONG** (≥58%, has beaten chance on recent unseen candles, both methods agree), **MODERATE** (≥55% with a proven edge),
  **WEAK** (close to a coin flip, so skip).
- It refreshes by itself at **every candle close**, so on 1m you get a new prediction every minute.
- Every prediction is graded automatically when its candle closes. The **live track record** shows how often it has been right in your browser.

**Live data:** your browser fetches the candles, order book and trades directly from Binance and sends them to
the agents, so predictions work even when Binance blocks the hosting server's region. If that fails, the server fetches the data itself.

**How the % is computed** (all on this coin's own last ~1000 candles):
1. Candlestick patterns: engulfing, hammer, shooting star, doji, three soldiers/crows, inside bar, 20-candle breakouts
2. Pattern matching: the 40 past moments whose recent candles looked most like now, and what the next candle did
3. An indicator model that learns from the agents' signals (trend, momentum, price action, volume, taker flow, higher-timeframe trend)
4. The two are blended, each weighted by how accurate it was on held-out recent candles
5. A walk-forward test on candles the method never saw decides whether there is a proven edge
6. Live order flow and the Chief Strategist can downgrade a call they strongly disagree with

**No one-sided bias:** the model ignores candles that close flat, and gives UP and DOWN examples equal weight,
so neither flat candles nor a recent trend can make it say SHORT (or LONG) every time. The direction has to come from the signals.
A regression test checks this on flat-candle, downtrend and uptrend data. The card also shows the market's own drift
("x% of the last 200 candles closed up"), and the track record shows how many LONG vs SHORT calls were made.

> One-candle moves, especially on 1m, are close to random, so honest probabilities are usually 50–60%.
> On pure random data this system labels every call WEAK. It doesn't invent an edge.
> On 1m and 5m a typical candle often moves less than trading fees cost, and the card warns you when that's the case.

CLI: `python -m crypto_agents next BTCUSDT --tf 1m --watch` prints a new prediction at every candle close.

## Features

| Feature | Where |
|---|---|
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
  forecast.py          next-candle prediction: candlestick patterns, pattern matching, indicator model, edge test
  ai.py                Claude chart-vision and senior-trader agents
  backtest.py          longer walk-forward backtest (CLI)
  report.py            console output
  web_page.py          browser UI
```
