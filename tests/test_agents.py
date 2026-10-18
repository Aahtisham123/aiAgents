import numpy as np
import pandas as pd

from crypto_agents import Strategist, data
from crypto_agents.backtest import backtest
from crypto_agents.report import render


def trending(direction: int, n: int = 3000) -> pd.DataFrame:
    df = data.synthetic_candles(n=n, seed=1)
    drift = np.exp(np.cumsum(np.full(n, 0.002 * direction)))
    for col in ("open", "high", "low", "close"):
        df[col] = df[col] * drift
    return df


def test_agents_score_ranges():
    snap = data.snapshot_from_hourly("TEST", data.synthetic_candles())
    d = Strategist().decide(snap)
    assert d.action in {"LONG", "SHORT", "NO TRADE"}
    assert len(d.reports) == 5
    for r in d.reports:
        assert -1 <= r.score <= 1 and 0 <= r.confidence <= 1
    assert 0 <= d.setup_quality <= 100
    assert "NOT FINANCIAL ADVICE" in render(d)


def test_strong_uptrend_is_never_shorted_and_plan_is_consistent():
    snap = data.snapshot_from_hourly("UP", trending(+1), funding_rate=0.0001, fear_greed=55)
    d = Strategist().decide(snap)
    assert d.reports[0].score > 0.5
    assert d.action != "SHORT"
    if d.plan:
        assert d.plan.stop_loss < d.plan.entry < d.plan.take_profits[0]
        assert abs(d.plan.risk_amount - 10) < 1e-9  # 1% of 1000


def test_strong_downtrend_is_never_longed():
    snap = data.snapshot_from_hourly("DOWN", trending(-1))
    d = Strategist().decide(snap)
    assert d.reports[0].score < -0.5
    assert d.action != "LONG"
    if d.plan:
        assert d.plan.take_profits[0] < d.plan.entry < d.plan.stop_loss


def test_sentiment_is_contrarian_at_extremes():
    from crypto_agents.agents import SentimentAgent
    base = data.snapshot_from_hourly("X", data.synthetic_candles(n=500))
    base.funding_rate, base.fear_greed, base.long_short_ratio = 0.001, 90, 3.0
    assert SentimentAgent().analyze(base).score < -0.5


def test_backtest_runs():
    res = backtest(data.synthetic_candles(n=2200), step=12, warmup=1500)
    s = res.summary
    assert s["trades"] == 0 or 0 <= s["win_rate_%"] <= 100
