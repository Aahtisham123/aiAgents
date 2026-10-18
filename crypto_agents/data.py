"""Market data: live candles / funding / sentiment from public APIs (no API key needed),
plus a synthetic generator for offline demos and tests."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import requests

BINANCE_SPOT = "https://api.binance.com"
BINANCE_FUTURES = "https://fapi.binance.com"
FEAR_GREED = "https://api.alternative.me/fng/?limit=2"

# Higher timeframe first: the trend agent weighs the bigger picture more.
DEFAULT_TIMEFRAMES = ("1d", "4h", "1h")


@dataclass
class MarketSnapshot:
    symbol: str
    candles: dict[str, pd.DataFrame]  # timeframe -> OHLCV, oldest first
    funding_rate: float | None = None  # last perpetual funding rate, e.g. 0.0001 = 0.01%
    open_interest_change: float | None = None  # % change of OI over the last ~24h
    long_short_ratio: float | None = None  # global accounts long/short ratio
    fear_greed: int | None = None  # 0 (extreme fear) .. 100 (extreme greed)
    notes: list[str] = field(default_factory=list)

    @property
    def entry_timeframe(self) -> str:
        return list(self.candles)[-1]

    @property
    def price(self) -> float:
        return float(self.candles[self.entry_timeframe]["close"].iloc[-1])


def _get(url: str, params: dict | None = None, timeout: int = 10):
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def fetch_klines(symbol: str, interval: str, limit: int = 500) -> pd.DataFrame:
    rows = _get(f"{BINANCE_SPOT}/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    df = pd.DataFrame(
        rows,
        columns=["open_time", "open", "high", "low", "close", "volume",
                 "close_time", "qv", "trades", "tbb", "tbq", "ignore"],
    )
    df = df[["open_time", "open", "high", "low", "close", "volume"]].astype(float)
    df.index = pd.to_datetime(df.pop("open_time"), unit="ms", utc=True)
    return df


def fetch_snapshot(symbol: str = "BTCUSDT", timeframes=DEFAULT_TIMEFRAMES, limit: int = 500) -> MarketSnapshot:
    symbol = symbol.upper()
    snap = MarketSnapshot(symbol, {tf: fetch_klines(symbol, tf, limit) for tf in timeframes})

    # Derivatives and sentiment data are optional: the agents still work without them.
    try:
        snap.funding_rate = float(_get(f"{BINANCE_FUTURES}/fapi/v1/premiumIndex", {"symbol": symbol})["lastFundingRate"])
    except Exception as exc:  # noqa: BLE001
        snap.notes.append(f"funding rate unavailable ({exc.__class__.__name__})")
    try:
        oi = _get(f"{BINANCE_FUTURES}/futures/data/openInterestHist", {"symbol": symbol, "period": "1h", "limit": 25})
        first, last = float(oi[0]["sumOpenInterest"]), float(oi[-1]["sumOpenInterest"])
        snap.open_interest_change = (last - first) / first * 100
    except Exception as exc:  # noqa: BLE001
        snap.notes.append(f"open interest unavailable ({exc.__class__.__name__})")
    try:
        ls = _get(f"{BINANCE_FUTURES}/futures/data/globalLongShortAccountRatio", {"symbol": symbol, "period": "1h", "limit": 1})
        snap.long_short_ratio = float(ls[-1]["longShortRatio"])
    except Exception as exc:  # noqa: BLE001
        snap.notes.append(f"long/short ratio unavailable ({exc.__class__.__name__})")
    try:
        snap.fear_greed = int(_get(FEAR_GREED)["data"][0]["value"])
    except Exception as exc:  # noqa: BLE001
        snap.notes.append(f"fear & greed index unavailable ({exc.__class__.__name__})")
    return snap


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


def synthetic_candles(n: int = 3000, seed: int = 7, start_price: float = 60_000.0) -> pd.DataFrame:
    """Hourly random-walk candles with drifting regimes. For demos/tests only — not real market data."""
    rng = np.random.default_rng(seed)
    drift = np.repeat(rng.normal(0, 0.0015, n // 200 + 1), 200)[:n]
    rets = drift + rng.normal(0, 0.008, n)
    close = start_price * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[start_price], close[:-1]])
    spread = np.abs(rng.normal(0, 0.004, n)) * close
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.lognormal(6, 0.5, n) * (1 + 20 * np.abs(rets))
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


def snapshot_from_hourly(symbol: str, hourly: pd.DataFrame, **extra) -> MarketSnapshot:
    """Build a 1d/4h/1h snapshot from hourly candles (used for CSV, synthetic data and backtests)."""
    return MarketSnapshot(
        symbol,
        {"1d": resample(hourly, "1D"), "4h": resample(hourly, "4h"), "1h": hourly},
        **extra,
    )
