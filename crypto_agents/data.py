"""Market data from free public APIs (no API key needed), plus synthetic data for offline demos/tests.

Sources
- Binance spot: candles (the last candle is the live, still-forming one), order book, recent trades, 24h tickers
- Binance USDⓈ-M futures: funding rate, open interest, long/short account ratio
- alternative.me: Crypto Fear & Greed index
- CoinGecko: total market cap change and BTC dominance
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import requests

# Tried in order. Binance blocks some regions (e.g. US servers); the others are fallbacks.
SPOT_HOSTS = ("https://api.binance.com", "https://data-api.binance.vision", "https://api.binance.us")
BINANCE_FUTURES = "https://fapi.binance.com"
FEAR_GREED = "https://api.alternative.me/fng/?limit=2"
COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"

# Entry timeframe -> the timeframes the agents read, higher timeframe first.
PROFILES = {
    "1m": ("15m", "5m", "1m"),
    "5m": ("1h", "15m", "5m"),
    "15m": ("4h", "1h", "15m"),
    "1h": ("1d", "4h", "1h"),
    "4h": ("1w", "1d", "4h"),
    "1d": ("1w", "1d"),
}
DEFAULT_TIMEFRAMES = PROFILES["1h"]
TF_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800}
PANDAS_RULE = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D", "1w": "1W"}

STABLE_BASES = {"USDC", "FDUSD", "TUSD", "BUSD", "DAI", "USDP", "USDE", "EUR", "AEUR", "EURI", "USD1",
                "PAXG", "XUSD", "BFUSD", "RLUSD", "USDS", "PYUSD"}


@dataclass
class MarketSnapshot:
    symbol: str
    candles: dict[str, pd.DataFrame]  # timeframe -> OHLCV, oldest first; last row may be the live candle
    funding_rate: float | None = None  # last perpetual funding rate, e.g. 0.0001 = 0.01%
    open_interest_change: float | None = None  # % change of open interest over the recent window
    long_short_ratio: float | None = None  # global accounts long/short ratio
    fear_greed: int | None = None  # 0 (extreme fear) .. 100 (extreme greed)
    market: dict | None = None  # CoinGecko global: market_cap_change_24h, btc_dominance
    orderflow: dict | None = None  # order book + recent trades summary, see fetch_orderflow
    fetched_at: float = field(default_factory=time.time)
    notes: list[str] = field(default_factory=list)

    @property
    def entry_timeframe(self) -> str:
        return list(self.candles)[-1]

    @property
    def price(self) -> float:
        return float(self.candles[self.entry_timeframe]["close"].iloc[-1])


# ---------------------------------------------------------------- HTTP with a small TTL cache

_cache: dict[tuple, tuple[float, object]] = {}
_cache_lock = threading.Lock()
_session = requests.Session()


def _get(url: str, params: dict | None = None, timeout: int = 10, ttl: float = 0):
    key = (url, tuple(sorted((params or {}).items())))
    if ttl:
        with _cache_lock:
            hit = _cache.get(key)
        if hit and time.time() - hit[0] < ttl:
            return hit[1]
    resp = _session.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if ttl:
        with _cache_lock:
            _cache[key] = (time.time(), data)
    return data


def _spot(path: str, params: dict | None = None, ttl: float = 0):
    errors = []
    for host in SPOT_HOSTS:
        try:
            return _get(f"{host}{path}", params, ttl=ttl)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 400:
                raise ValueError(f"Unknown symbol {params.get('symbol') if params else ''!r}") from exc
            errors.append(f"{host.split('//')[1]} (HTTP {exc.response.status_code if exc.response is not None else '?'})")
        except requests.RequestException as exc:
            errors.append(f"{host.split('//')[1]} ({exc.__class__.__name__})")
    raise ConnectionError("Could not reach Binance — tried " + ", ".join(errors)
                          + ". If you deployed on Vercel, keep the fra1 region in vercel.json.")


# ---------------------------------------------------------------- live data

def fetch_klines(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    rows = _spot("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit}, ttl=2)
    df = pd.DataFrame(
        rows,
        columns=["open_time", "open", "high", "low", "close", "volume",
                 "close_time", "qv", "trades", "tbb", "tbq", "ignore"],
    )
    df = df[["open_time", "open", "high", "low", "close", "volume", "tbb"]].astype(float)
    df = df.rename(columns={"tbb": "taker_buy_volume"})
    df.index = pd.to_datetime(df.pop("open_time"), unit="ms", utc=True)
    return df


def fetch_orderflow(symbol: str) -> dict:
    """Order-book imbalance and taker buy/sell flow from the most recent ~1000 trades."""
    book = _spot("/api/v3/depth", {"symbol": symbol, "limit": 500}, ttl=1)
    bids = np.array(book["bids"], dtype=float)
    asks = np.array(book["asks"], dtype=float)
    mid = (bids[0, 0] + asks[0, 0]) / 2

    def depth(side, pct):
        if side is bids:
            m = bids[:, 0] >= mid * (1 - pct / 100)
            return float((bids[m, 0] * bids[m, 1]).sum())
        m = asks[:, 0] <= mid * (1 + pct / 100)
        return float((asks[m, 0] * asks[m, 1]).sum())

    bid1, ask1 = depth(bids, 1.0), depth(asks, 1.0)
    bid02, ask02 = depth(bids, 0.2), depth(asks, 0.2)

    trades = _spot("/api/v3/aggTrades", {"symbol": symbol, "limit": 1000}, ttl=1)
    qty = np.array([float(t["q"]) * float(t["p"]) for t in trades])
    is_sell = np.array([t["m"] for t in trades])  # buyer is maker -> the aggressor sold
    buy, sell = float(qty[~is_sell].sum()), float(qty[is_sell].sum())
    big = qty >= np.quantile(qty, 0.98) if len(qty) > 50 else np.zeros(len(qty), bool)
    span = (trades[-1]["T"] - trades[0]["T"]) / 1000 if trades else 0
    return {
        "mid": float(mid),
        "spread_pct": float((asks[0, 0] - bids[0, 0]) / mid * 100),
        "book_imbalance_1pct": (bid1 - ask1) / (bid1 + ask1) if bid1 + ask1 else 0.0,
        "book_imbalance_0_2pct": (bid02 - ask02) / (bid02 + ask02) if bid02 + ask02 else 0.0,
        "bid_depth_1pct": bid1, "ask_depth_1pct": ask1,
        "taker_buy_ratio": buy / (buy + sell) if buy + sell else 0.5,
        "whale_buy": float(qty[big & ~is_sell].sum()), "whale_sell": float(qty[big & is_sell].sum()),
        "trades_window_sec": float(span), "trades": len(trades),
    }


def fetch_market_context() -> dict | None:
    try:
        g = _get(COINGECKO_GLOBAL, ttl=300)["data"]
        return {"market_cap_change_24h": float(g["market_cap_change_percentage_24h_usd"]),
                "btc_dominance": float(g["market_cap_percentage"]["btc"])}
    except Exception:  # noqa: BLE001
        return None


def fetch_snapshot(symbol: str = "BTCUSDT", timeframe: str = "1h", limit: int = 500,
                   orderflow: bool = True) -> MarketSnapshot:
    symbol = symbol.upper()
    if timeframe not in PROFILES:
        raise ValueError(f"Unsupported timeframe {timeframe!r}. Use one of {', '.join(PROFILES)}")
    snap = MarketSnapshot(symbol, {tf: fetch_klines(symbol, tf, limit) for tf in PROFILES[timeframe]})
    period = "5m" if timeframe in ("1m", "5m", "15m") else "1h"

    # Everything below is optional: the agents still work without it.
    def optional(label, fn):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            snap.notes.append(f"{label} unavailable ({exc.__class__.__name__})")
            return None

    snap.funding_rate = optional("funding rate", lambda: float(_get(
        f"{BINANCE_FUTURES}/fapi/v1/premiumIndex", {"symbol": symbol}, ttl=30)["lastFundingRate"]))

    def oi_change():
        oi = _get(f"{BINANCE_FUTURES}/futures/data/openInterestHist",
                  {"symbol": symbol, "period": period, "limit": 25}, ttl=30)
        first, last = float(oi[0]["sumOpenInterest"]), float(oi[-1]["sumOpenInterest"])
        return (last - first) / first * 100
    snap.open_interest_change = optional("open interest", oi_change)
    snap.long_short_ratio = optional("long/short ratio", lambda: float(_get(
        f"{BINANCE_FUTURES}/futures/data/globalLongShortAccountRatio",
        {"symbol": symbol, "period": period, "limit": 1}, ttl=30)[-1]["longShortRatio"]))
    snap.fear_greed = optional("fear & greed index", lambda: int(_get(FEAR_GREED, ttl=600)["data"][0]["value"]))
    snap.market = fetch_market_context()
    if orderflow:
        snap.orderflow = optional("order flow", lambda: fetch_orderflow(symbol))
    return snap


def top_symbols(n: int = 20, quote: str = "USDT") -> list[dict]:
    """The most traded spot pairs by 24h quote volume (stablecoins and leveraged tokens excluded)."""
    rows = _spot("/api/v3/ticker/24hr", ttl=30)
    out = []
    for r in rows:
        sym = r["symbol"]
        if not sym.endswith(quote):
            continue
        base = sym[: -len(quote)]
        if base in STABLE_BASES or base.endswith(("UP", "DOWN", "BULL", "BEAR")) or float(r["lastPrice"]) == 0:
            continue
        out.append({"symbol": sym, "price": float(r["lastPrice"]),
                    "change_24h": float(r["priceChangePercent"]), "volume_24h": float(r["quoteVolume"])})
    out.sort(key=lambda r: -r["volume_24h"])
    return out[:n]


# ---------------------------------------------------------------- offline data

def load_csv(path: str) -> pd.DataFrame:
    """Load OHLCV exported from TradingView/exchange. Needs time,open,high,low,close,volume columns."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    time_col = next(c for c in df.columns if c in ("time", "timestamp", "date", "open_time"))
    ts = df.pop(time_col)
    df.index = pd.to_datetime(ts, unit="s", utc=True) if np.issubdtype(ts.dtype, np.number) else pd.to_datetime(ts, utc=True)
    if "volume" not in df.columns:
        df["volume"] = 1.0
    return df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    return df.resample(rule).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna()


def synthetic_candles(n: int = 3000, seed: int = 7, start_price: float = 60_000.0, freq: str = "1h") -> pd.DataFrame:
    """Random-walk candles with drifting regimes. For demos/tests only — not real market data."""
    rng = np.random.default_rng(seed)
    drift = np.repeat(rng.normal(0, 0.0015, n // 200 + 1), 200)[:n]
    rets = drift + rng.normal(0, 0.008, n)
    close = start_price * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[start_price], close[:-1]])
    spread = np.abs(rng.normal(0, 0.004, n)) * close
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.lognormal(6, 0.5, n) * (1 + 20 * np.abs(rets))
    idx = pd.date_range("2024-01-01", periods=n, freq=freq, tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def snapshot_from_base(symbol: str, base: pd.DataFrame, timeframe: str = "1h", **extra) -> MarketSnapshot:
    """Build a multi-timeframe snapshot by resampling candles of the entry timeframe."""
    tfs = PROFILES[timeframe]
    candles = {tf: base if tf == timeframe else resample(base, PANDAS_RULE[tf]) for tf in tfs}
    return MarketSnapshot(symbol, candles, **extra)


def snapshot_from_hourly(symbol: str, hourly: pd.DataFrame, **extra) -> MarketSnapshot:
    return snapshot_from_base(symbol, hourly, "1h", **extra)


def demo_snapshot(symbol: str, timeframe: str = "1h") -> MarketSnapshot:
    freq = PANDAS_RULE[timeframe]
    # Enough entry candles that every higher timeframe has history.
    n = {"1m": 6000, "5m": 6000, "15m": 6000, "1h": 3000, "4h": 3000, "1d": 2000}[timeframe]
    return snapshot_from_base(symbol, synthetic_candles(n=n, freq=freq), timeframe)
