# Crypto Trading Agents

Five analysis agents work through a trader's pre-trade checklist. A **Chief Strategist** combines their
votes into one decision: **LONG**, **SHORT** or **NO TRADE**. Each trade plan comes with an entry,
a stop-loss, three take-profits and a position size.

> ⚠️ **No signal is 100% accurate.** Nobody can predict crypto prices with certainty. Anyone who promises
> "100% winning signals" is wrong or running a scam. This tool tells you whether a setup lines up and
> manages your risk; it does not tell you the future. Run the backtest to see its real win rate
> before you trade with real money. This is not financial advice.

## The agents

| # | Agent | What it checks |
|---|-------|----------------|
| 1 | **Trend Analyst** | EMA 20/50/200 stack, ADX trend strength, +DI/-DI on 1D, 4H and 1H. Higher timeframes count more. |
| 2 | **Momentum Analyst** | RSI (zones, overbought/oversold), MACD histogram and crosses, Stochastic RSI, RSI divergences |
| 3 | **Price Action & Volume Analyst** | Support/resistance from swing pivots, range breakouts with volume, VWAP, OBV confirmation, Bollinger squeeze |
| 4 | **Sentiment & Derivatives Analyst** | Futures funding rate, open-interest change, long/short ratio, Fear & Greed index (contrarian at extremes) |
| 5 | **Risk Manager** | Volatility regime (ATR), stop placement behind S/R, take-profits at 1.5R/2.5R/4R, position size from your account and risk %. Can **veto** a trade. |
| ★ | **Chief Strategist** | Weighted vote (trend 35%, momentum 25%, structure 25%, sentiment 15%) |

The strategist only signals a trade when **all** of these hold:
- the combined score is strong enough (|score| ≥ 0.3)
- at least 3 analysts agree
- the trade does not fight the higher-timeframe trend
- the Risk Manager has not vetoed it

If any of these fails, the answer is **NO TRADE**. Staying out is a valid decision.

The indicators use the same formulas as TradingView's built-ins (RSI, MACD, ADX, ATR, Bollinger, VWAP, OBV).
TradingView has no public API for charts, so the agents pull candles straight from Binance's public API.
You can also feed them a CSV exported from TradingView.

## Setup

```bash
pip install -r requirements.txt
```

No API keys are needed. Everything uses public market data.

## Usage

```bash
# Full multi-agent analysis with live data
python -m crypto_agents analyze BTCUSDT ETHUSDT

# Your own account size and risk per trade (default 1000 USDT, 1%)
python -m crypto_agents analyze SOLUSDT --account 5000 --risk 0.5

# Scan many coins and rank the setups
python -m crypto_agents scan
python -m crypto_agents scan BTCUSDT ETHUSDT PEPEUSDT

# Measure the historical win rate (live: last ~1000 hourly candles)
python -m crypto_agents backtest --symbol BTCUSDT
# Better: 1–2 years of hourly candles exported from TradingView (time,open,high,low,close,volume)
python -m crypto_agents backtest --csv BTCUSDT_1h.csv

# Offline demo with synthetic data
python -m crypto_agents analyze BTCUSDT --demo
python -m crypto_agents backtest --demo
```

### How to read the output
- **Setup quality (0–100)** counts how many boxes are ticked. It is **not** a win probability.
- **R** means "multiples of the amount you risked". If you risk 10 USDT, +2R = +20 USDT and -1R = -10 USDT.
  With 2R targets, a strategy that wins only 40% of the time still makes money.
- At TP1, take partial profit and move your stop to break-even.

## Tests

```bash
python -m pytest -q
```

## Project layout

```
crypto_agents/
  data.py          live Binance data, Fear & Greed, CSV loader, synthetic data
  indicators.py    RSI, MACD, Stoch RSI, ADX, ATR, Bollinger, VWAP, OBV, swing levels
  agents/          trend, momentum, structure, sentiment, risk
  strategist.py    combines the agents into a decision
  backtest.py      walk-forward backtest
  report.py        console report
```
