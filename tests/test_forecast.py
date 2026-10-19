import numpy as np
import pytest
import pandas as pd

from crypto_agents import Strategist, data
from crypto_agents.forecast import build_features, next_candle


def candles(seed: int, signal: float, n: int = 1000, freq: str = "1min") -> pd.DataFrame:
    """Random walk; with `signal` > 0 the next candle follows the sign of the taker-buy imbalance."""
    rng = np.random.default_rng(seed)
    tb = rng.uniform(0.3, 0.7, n)
    rets = rng.normal(0, 0.003, n)
    rets[1:] += signal * 0.003 * np.sign(tb[:-1] - 0.5)
    close = 100 * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[100], close[:-1]])
    vol = rng.lognormal(6, 0.5, n)
    return pd.DataFrame({"open": open_, "high": np.maximum(open_, close) * 1.001,
                         "low": np.minimum(open_, close) * 0.999, "close": close, "volume": vol,
                         "taker_buy_volume": vol * tb},
                        index=pd.date_range("2024-01-01", periods=n, freq=freq, tz="UTC"))


def test_finds_a_real_pattern_and_calls_the_right_direction():
    df = candles(3, signal=1.0)
    f = next_candle(data.snapshot_from_base("X", df, "1m"))
    assert f["has_edge"] and f["model_test"]["call_accuracy"] > 0.6
    expected = "LONG" if df["taker_buy_volume"].iloc[-1] / df["volume"].iloc[-1] > 0.5 else "SHORT"
    assert f["direction"] == expected
    assert (f["probability_up"] > 0.5) == (expected == "LONG")
    assert f["strength"] in ("STRONG", "MODERATE") and f["action"] == expected
    assert abs(f["probability_up"] + f["probability_down"] - 1) < 1e-9


def test_pure_noise_rarely_claims_an_edge():
    edges = sum(next_candle(data.snapshot_from_base("N", candles(s, 0.0), "1m"))["has_edge"] for s in range(10))
    assert edges <= 2  # a 95% test should be fooled about 1 time in 20
    for seed in range(5):
        f = next_candle(data.snapshot_from_base("N", candles(seed, 0.0), "1m"))
        assert f["direction"] in ("LONG", "SHORT") and 0.5 <= f["chance"] <= 1  # always gives an answer
        if not f["has_edge"]:
            assert f["strength"] != "STRONG"


def test_features_never_use_future_candles():
    df = candles(1, 0.5)
    snap = data.snapshot_from_base("X", df, "1m")
    before = build_features(snap, df).iloc[:700]
    changed = df.copy()
    changed.iloc[700:, :4] *= 3  # rewrite the "future"
    snap2 = data.snapshot_from_base("X", changed, "1m")
    after = build_features(snap2, changed).iloc[:700]
    pd.testing.assert_frame_equal(before, after)


def test_forecast_targets_the_forming_candle():
    df = candles(2, 0.5)
    snap = data.snapshot_from_base("X", df, "1m")
    last_open = df.index[-1].timestamp()
    f = next_candle(snap, now=last_open + 20)  # 20 s into the live candle
    assert f["target_candle_open"] == last_open and f["seconds_elapsed"] == 20
    f = next_candle(snap, now=last_open + 50)
    assert any("already" in w for w in f["warnings"])
    f = next_candle(snap, now=last_open + 200)  # all candles closed -> forecast the next one
    assert f["target_candle_open"] == last_open + 60


def test_strategist_and_orderflow_can_veto():
    df = candles(3, signal=1.0)
    snap = data.snapshot_from_base("X", df, "1m")
    f = next_candle(snap)
    assert f["action"] in ("LONG", "SHORT")
    sign = 1 if f["direction"] == "LONG" else -1
    snap.orderflow = {"mid": 1.0, "spread_pct": 0.01, "book_imbalance_1pct": -0.9 * sign,
                      "book_imbalance_0_2pct": 0, "bid_depth_1pct": 1, "ask_depth_1pct": 1,
                      "taker_buy_ratio": 0.5 - 0.45 * sign, "whale_buy": 0, "whale_sell": 0,
                      "trades_window_sec": 30, "trades": 1000}
    vetoed = next_candle(snap, Strategist().decide(snap))
    assert vetoed["strength"] == "WEAK" and vetoed["action"] == "NO TRADE"
    assert any("order flow disagrees" in w for w in vetoed["warnings"])


def test_next_endpoint_demo():
    import app as webapp
    j = webapp.app.test_client().get("/api/next?symbol=BTCUSDT&tf=1m&demo=1").get_json()
    f = j["forecast"]
    assert f["direction"] in {"LONG", "SHORT"} and 0 <= f["probability_up"] <= 1
    assert j["decision"]["symbol"] == "BTCUSDT" and f["trained_on"] >= 200


def binance_rows(df):
    return [[int(t.timestamp() * 1000), r.open, r.high, r.low, r.close, r.volume, r.taker_buy_volume]
            for t, r in df.iterrows()]


def test_next_endpoint_uses_live_candles_sent_by_the_browser():
    import app as webapp
    df = candles(3, signal=1.0, n=1000, freq="1min")
    snap = data.snapshot_from_base("X", df, "1m")
    live = {"klines": {tf: binance_rows(c.assign(taker_buy_volume=c.get("taker_buy_volume", c["volume"] / 2)))
                       for tf, c in snap.candles.items()},
            "depth": {"bids": [["99.9", "5"], ["99.8", "5"]], "asks": [["100.1", "1"], ["100.2", "1"]]},
            "trades": [{"p": "100", "q": "1", "m": i % 3 == 0, "T": 1700000000000 + i} for i in range(300)]}
    client = webapp.app.test_client()
    j = client.post("/api/next", json={"symbol": "BTCUSDT", "tf": "1m", "live": live}).get_json()
    f = j["forecast"]
    assert any("browser" in n for n in f["data_notes"])
    assert f["direction"] in {"LONG", "SHORT"} and f["trained_on"] > 500
    of = next(r for r in j["decision"]["reports"] if r["agent"] == "Order Flow Analyst")
    assert of["confidence"] > 0  # order book + trades from the browser were used
    o = client.post("/api/odds", json={"symbol": "BTCUSDT", "tf": "1m", "live": live}).get_json()
    assert 0 <= o["chance_up"] <= 1
    bad = client.post("/api/next", json={"symbol": "BTCUSDT", "tf": "1m", "live": {"klines": {"1m": []}}})
    assert bad.status_code == 400


def test_candlestick_patterns():
    from crypto_agents.forecast import detect_patterns
    idx = pd.date_range("2024-01-01", periods=4, freq="1min", tz="UTC")
    df = pd.DataFrame({"open": [10, 10, 10.5, 9.0], "high": [10.2, 10.6, 10.6, 11.2],
                       "low": [9.8, 9.9, 9.4, 8.9], "close": [10.1, 10.5, 9.5, 11.0],
                       "volume": [1, 1, 1, 1]}, index=idx)
    p = detect_patterns(df)
    assert p["bullish_engulfing"].iloc[3] and not p["bearish_engulfing"].iloc[3]
    assert p["bearish_engulfing"].iloc[2]
    hammer = pd.DataFrame({"open": [10.0], "high": [10.12], "low": [9.5], "close": [10.1], "volume": [1]}, index=idx[:1])
    assert detect_patterns(hammer)["hammer"].iloc[0]


def test_pattern_matching_learns_a_repeating_shape():
    """After two green candles the next is usually red: pattern matching should pick that up."""
    rng = np.random.default_rng(5)
    n, rets = 1000, []
    for i in range(n):
        if len(rets) >= 2 and rets[-1] > 0 and rets[-2] > 0:
            rets.append(-abs(rng.normal(0.003, 0.001)) if rng.random() < 0.8 else abs(rng.normal(0.003, 0.001)))
        else:
            rets.append(rng.normal(0, 0.003))
    close = 100 * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[100], close[:-1]])
    df = pd.DataFrame({"open": open_, "high": np.maximum(open_, close) * 1.0005, "low": np.minimum(open_, close) * 0.9995,
                       "close": close, "volume": np.ones(n), "taker_buy_volume": np.full(n, 0.5)},
                      index=pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC"))
    # make the last two candles green
    df.iloc[-2:, df.columns.get_loc("close")] = df["open"].iloc[-2:] * 1.003
    df.iloc[-2:, df.columns.get_loc("high")] = df["close"].iloc[-2:] * 1.0005
    df.iloc[-1, df.columns.get_loc("open")] = df["close"].iloc[-2]
    df.iloc[-1, df.columns.get_loc("close")] = df["open"].iloc[-1] * 1.003
    df.iloc[-1, df.columns.get_loc("high")] = df["close"].iloc[-1] * 1.0005
    f = next_candle(data.snapshot_from_base("P", df, "5m"), now=df.index[-1].timestamp() + 600)
    assert f["pattern_match_up"] < 0.4 and f["direction"] == "SHORT"


def _walk(seed, drift=0.0, tick=None, n=1200):
    rng = np.random.default_rng(seed)
    close = 0.1 * np.exp(np.cumsum(rng.normal(drift, 0.002, n)))
    open_ = np.concatenate([[0.1], close[:-1]])
    df = pd.DataFrame({"open": open_, "high": np.maximum(open_, close) * 1.001,
                       "low": np.minimum(open_, close) * 0.999, "close": close},
                      index=pd.date_range("2024-01-01", periods=n, freq="1min", tz="UTC"))
    if tick:
        df = (df / tick).round() * tick
        df["open"] = df["close"].shift().fillna(df["open"])
        df["high"] = df[["open", "high", "close"]].max(axis=1)
        df["low"] = df[["open", "low", "close"]].min(axis=1)
    vol = rng.lognormal(6, 0.5, n)
    return df.assign(volume=vol, taker_buy_volume=vol * rng.uniform(0.4, 0.6, n))


@pytest.mark.parametrize("kw", [{"tick": 0.0001}, {"drift": -0.0004}, {"drift": 0.0004}],
                         ids=["many flat candles", "downtrend", "uptrend"])
def test_no_one_sided_bias(kw):
    """Regression test: flat candles or a trend alone must not make every prediction SHORT (or LONG)."""
    df = _walk(1, **kw)
    calls = [next_candle(data.snapshot_from_base("X", df.iloc[:cut], "1m"),
                         now=df.index[cut - 1].timestamp() + 600)["direction"]
             for cut in range(1000, 1200, 10)]
    share_short = calls.count("SHORT") / len(calls)
    assert 0.2 <= share_short <= 0.8, f"{share_short:.0%} SHORT"
