import time

import numpy as np
import pandas as pd
import pytest

import app as webapp
from crypto_agents import data, protrader as pt
from crypto_agents.strategist import Strategist


def candles(closes, tf="5m", wick=0.002, start="2026-10-01"):
    closes = np.asarray(closes, float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    idx = pd.date_range(start, periods=len(closes), freq=data.PANDAS_RULE[tf], tz="UTC")
    return pd.DataFrame({"open": opens, "high": np.maximum(opens, closes) * (1 + wick),
                         "low": np.minimum(opens, closes) * (1 - wick), "close": closes,
                         "volume": 100.0}, index=idx)


def test_entry_needs_a_close_beyond_the_level_not_a_wick():
    rng = np.random.default_rng(1)
    base = 100 + rng.normal(0, 0.1, 200)
    df = candles(base)
    level = float(df["high"].iloc[-21:-1].max())
    df.iloc[-1, df.columns.get_loc("high")] = level * 1.01  # a wick far above the level, close stays inside
    df.iloc[-1, df.columns.get_loc("close")] = level * 0.999
    lvl = next(s for s in pt.entry_timer(df, "1h", "LONG", 24) if s["setup"] == "level")
    assert lvl["status"] == "WAITING"

    df.iloc[-1, df.columns.get_loc("close")] = level * 1.002  # now it closes above
    lvl = next(s for s in pt.entry_timer(df, "1h", "LONG", 24) if s["setup"] == "level")
    assert lvl["status"] == "TRIGGERED" and lvl["bars_ago"] == 0 and lvl["stop"] < lvl["trigger_price"]


def test_opening_range_breakout_of_the_utc_day():
    closes = [100] * 290 + [100, 100.5, 99.5] + [100.2] * 3 + [101.5]  # 3-bar range, then a close above it
    df = candles(closes, "5m", wick=0.001, start="2026-10-01 23:50")
    df = df[df.index >= "2026-10-02"].copy()
    df = pd.concat([candles([100] * 150, "5m", start="2026-10-01 11:20"), df])
    orb = next(s for s in pt.entry_timer(df, "5m", "LONG", 24) if s["setup"] == "orb")
    assert orb["status"] == "TRIGGERED"
    assert orb["opening_range"]["high"] == pytest.approx(100.5 * 1.001)
    assert "midpoint" in orb["stop_rule"]


def test_time_machine_checks_the_stop_first_and_is_repeatable():
    df = candles(100 + np.random.default_rng(3).normal(0, 0.3, 600).cumsum() * 0.1, "1h", wick=0.05)
    # every replayed candle spans ±5%: it touches both the stop and the target, which counts as the stop
    mc = pt.time_machine(df, "1h", "LONG", 100, 99, 101, steps=5, replays=2000)
    assert mc["p_stop"] == 1.0 and mc["p_target"] == 0.0
    a = pt.time_machine(df, "1h", "SHORT", 100, 104, 92, steps=10, replays=3000)
    b = pt.time_machine(df, "1h", "SHORT", 100, 104, 92, steps=10, replays=3000)
    assert a["p_target"] == b["p_target"] and a["seed"] == pt.SEED
    assert a["p_target"] + a["p_stop"] + a["p_neither"] == pytest.approx(1)
    assert len(a["fan"]) == 10


@pytest.mark.parametrize("pt_, ps, r, head", [
    (0.29, 0.25, 1.0, "Close to a coin flip"),       # the day-trader-skill's TSLA reel
    (0.30, 0.60, 2.0, "Close to break-even"),        # 2R only needs 1 in 3
    (0.40, 0.50, 2.0, "Leans toward the target"),
    (0.10, 0.60, 1.0, "Strongly toward the stop"),
])
def test_verdict_against_break_even(pt_, ps, r, head):
    assert pt.verdict({"p_target": pt_, "p_stop": ps, "r_at_target": r})[0].startswith(head)


def test_regime_scores_a_bull_stack_and_reads_funding():
    up = candles(np.linspace(50, 100, 420) * (1 + 0.01 * np.sin(np.arange(420))), "1d")
    snap = data.snapshot_from_base("ETHUSDT", candles(np.linspace(90, 100, 600), "1h"), "1h", funding_rate=0.0007)
    reg = pt.market_regime(snap, up, up)
    names = [c["name"] for c in reg["components"]]
    assert reg["score"] is not None and "BTC trend structure" in names and "Perpetual funding" in names
    assert next(c for c in reg["components"] if c["name"] == "BTC trend structure")["score"] == 100
    assert next(c for c in reg["components"] if c["name"] == "Perpetual funding")["score"] == 10
    assert pt.market_regime(snap, None, None)["zone"] == "UNKNOWN"


def test_circuit_breaker_and_discipline_gate_block_new_trades():
    now = time.time()
    losses = [{"closed": (now - 600 * i) * 1000, "pnl": -100.0, "symbol": "BTCUSDT"} for i in (3, 2, 1)]
    cb = pt.circuit_breaker({"start_equity": 100000, "trades": losses}, "5m", now)
    assert cb["recommendation"] == "COOLDOWN" and cb["streak"] == 3
    big = [{"closed": (now - 60) * 1000, "pnl": -2500.0, "symbol": "BTCUSDT"}]
    assert pt.circuit_breaker({"start_equity": 100000, "trades": big}, "1h", now)["recommendation"] == "HALTED"
    win = losses + [{"closed": (now - 30) * 1000, "pnl": 50.0, "symbol": "ETHUSDT"}]
    assert pt.circuit_breaker({"start_equity": 100000, "trades": win}, "5m", now)["recommendation"] == "TRADING_ALLOWED"

    snap = data.demo_snapshot("ETHUSDT", "15m")
    d = Strategist().decide(snap)
    p = pt.build_plan(snap, d, journal={"start_equity": 100000, "trades": big}, replays=500)
    assert p["action"] == "NO TRADE"
    assert {s["key"]: s["status"] for s in p["steps"]}["breaker"] == "FAIL"
    assert {s["key"]: s["status"] for s in p["steps"]}["gate"] == "FAIL"


@pytest.mark.parametrize("tf", ["1m", "5m", "15m", "1h", "4h", "1d"])
@pytest.mark.parametrize("side", ["LONG", "SHORT"])
def test_plan_levels_and_size_are_consistent(tf, side):
    snap = data.demo_snapshot("SOLUSDT", tf)
    d = Strategist(2000, 1).decide(snap)
    p = pt.build_plan(snap, d, account=2000, risk_pct=1, side=side, replays=500)
    assert not p.get("error")
    s = 1 if side == "LONG" else -1
    assert (p["entry"] - p["stop"]) * s > 0
    assert all((t - p["entry"]) * s > 0 for t in p["targets"])
    assert p["targets"][1] == pytest.approx(p["entry"] + s * 2 * abs(p["entry"] - p["stop"]), rel=1e-6)
    assert p["sizing"]["max_loss"] <= 2000 * 0.01 + 1e-6
    assert p["action"].split(" (")[0] in {"NO TRADE", f"ENTER {side} NOW", "WAIT FOR RETEST", f"WAIT FOR {side} TRIGGER"}
    assert p["how_to_enter"] and len(p["steps"]) >= 9


def test_plan_endpoints(monkeypatch):
    c = webapp.app.test_client()
    j = c.get("/api/plan?symbol=ethusdt&tf=5m&demo=1&side=SHORT&target_r=3").get_json()
    assert j["side"] == "SHORT" and j["target_r"] == 3
    assert [s["key"] for s in j["steps"]][:3] == ["regime", "technicals", "setups"]
    j = c.post("/api/next", json={"symbol": "BTCUSDT", "tf": "15m", "demo": "1",
                                  "journal": {"start_equity": 100000, "trades": []}}).get_json()
    assert "action" in j["plan"] and any(s["key"] == "forecast" for s in j["plan"]["steps"])
