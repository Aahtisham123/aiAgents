import numpy as np
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
    assert f["has_edge"] and f["model_test"]["call_accuracy"] > 0.65
    expected = "LONG" if df["taker_buy_volume"].iloc[-1] / df["volume"].iloc[-1] > 0.5 else "SHORT"
    assert f["action"] == expected
    assert (f["probability_up"] > 0.5) == (expected == "LONG")
    assert abs(f["probability_up"] + f["probability_down"] - 1) < 1e-9


def test_pure_noise_rarely_claims_an_edge():
    edges = sum(next_candle(data.snapshot_from_base("N", candles(s, 0.0), "1m"))["has_edge"] for s in range(10))
    assert edges <= 2  # a 95% test should be fooled about 1 time in 20
    f = next_candle(data.snapshot_from_base("N", candles(0, 0.0), "1m"))
    if not f["has_edge"]:
        assert f["action"] == "NO TRADE"


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
    assert any("Late entry" in r for r in f["reasons"])
    f = next_candle(snap, now=last_open + 200)  # all candles closed -> forecast the next one
    assert f["target_candle_open"] == last_open + 60


def test_strategist_and_orderflow_can_veto():
    df = candles(3, signal=1.0)
    snap = data.snapshot_from_base("X", df, "1m")
    f = next_candle(snap)
    assert f["action"] in ("LONG", "SHORT")
    sign = 1 if f["action"] == "LONG" else -1
    snap.orderflow = {"mid": 1.0, "spread_pct": 0.01, "book_imbalance_1pct": -0.9 * sign,
                      "book_imbalance_0_2pct": 0, "bid_depth_1pct": 1, "ask_depth_1pct": 1,
                      "taker_buy_ratio": 0.5 - 0.45 * sign, "whale_buy": 0, "whale_sell": 0,
                      "trades_window_sec": 30, "trades": 1000}
    vetoed = next_candle(snap, Strategist().decide(snap))
    assert vetoed["action"] == "NO TRADE" and vetoed["vetoes"]


def test_next_endpoint_demo():
    import app as webapp
    j = webapp.app.test_client().get("/api/next?symbol=BTCUSDT&tf=1m&demo=1").get_json()
    f = j["forecast"]
    assert f["action"] in {"LONG", "SHORT", "NO TRADE"} and 0 <= f["probability_up"] <= 1
    assert j["decision"]["symbol"] == "BTCUSDT" and f["trained_on"] >= 200
