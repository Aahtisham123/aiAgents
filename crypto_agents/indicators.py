"""Technical indicators (the same maths TradingView uses for its built-ins)."""
import numpy as np
import pandas as pd


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def rma(series: pd.Series, length: int) -> pd.Series:
    """Wilder's moving average, used by RSI / ATR / ADX."""
    return series.ewm(alpha=1 / length, adjust=False).mean()


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = rma(delta.clip(lower=0), length)
    loss = rma(-delta.clip(upper=0), length)
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def stoch_rsi(close: pd.Series, length: int = 14, k: int = 3, d: int = 3):
    r = rsi(close, length)
    lo, hi = r.rolling(length).min(), r.rolling(length).max()
    raw = 100 * (r - lo) / (hi - lo).replace(0, np.nan)
    k_line = raw.rolling(k).mean()
    return k_line, k_line.rolling(d).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift()
    return pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return rma(true_range(df), length)


def adx(df: pd.DataFrame, length: int = 14):
    """Returns (adx, +DI, -DI)."""
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = rma(true_range(df), length)
    plus_di = 100 * rma(plus_dm, length) / tr
    minus_di = 100 * rma(minus_dm, length) / tr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return rma(dx.fillna(0), length), plus_di, minus_di


def bollinger(close: pd.Series, length: int = 20, mult: float = 2.0):
    mid = sma(close, length)
    std = close.rolling(length).std()
    return mid - mult * std, mid, mid + mult * std


def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff()).fillna(0)
    return (direction * df["volume"]).cumsum()


def vwap(df: pd.DataFrame, length: int = 24) -> pd.Series:
    """Rolling VWAP over the last `length` candles."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    pv = (typical * df["volume"]).rolling(length).sum()
    return pv / df["volume"].rolling(length).sum()


def swing_levels(df: pd.DataFrame, window: int = 5, lookback: int = 150):
    """Pivot highs/lows over the recent `lookback` candles -> (supports, resistances)."""
    recent = df.tail(lookback)
    highs, lows = recent["high"].values, recent["low"].values
    res, sup = [], []
    for i in range(window, len(recent) - window):
        if highs[i] == highs[i - window : i + window + 1].max():
            res.append(float(highs[i]))
        if lows[i] == lows[i - window : i + window + 1].min():
            sup.append(float(lows[i]))
    return sorted(sup), sorted(res)
