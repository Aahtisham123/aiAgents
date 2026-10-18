import base64
from types import SimpleNamespace

import pytest

import app as webapp
from crypto_agents import ai


@pytest.fixture
def client():
    return webapp.app.test_client()


@pytest.mark.parametrize("tf", ["5m", "1h"])
def test_analyze_demo(client, tf):
    r = client.get(f"/api/analyze?symbol=btcusdt&tf={tf}&demo=1&account=500&risk=2")
    assert r.status_code == 200
    j = r.get_json()
    assert j["symbol"] == "BTCUSDT" and j["timeframe"] == tf
    assert j["action"] in {"LONG", "SHORT", "NO TRADE"}
    assert len(j["reports"]) == 6 and "bias" in j["reports"][0]
    assert j["strategy"] and j["horizon_text"]


def test_bad_timeframe(client):
    assert client.get("/api/analyze?tf=7m&demo=1").status_code == 400


def test_odds_demo(client):
    j = client.get("/api/odds?symbol=ETHUSDT&tf=15m&demo=1").get_json()
    assert 0 <= j["chance_up"] <= 1 and j["windows_tested"] > 50
    assert j["all_signals"]["signals"] >= 0


def test_scan_demo_and_index(client):
    j = client.get("/api/scan?symbols=AAAUSDT,BBB&demo=1&tf=5m").get_json()
    assert [r["symbol"] for r in j["results"]] == ["AAAUSDT", "BBBUSDT"] or len(j["results"]) == 2
    assert all("action" in r for r in j["results"])
    assert b"Crypto Trading Agents" in client.get("/").data


@pytest.mark.parametrize("raw,expected", [
    ("BINANCE:BTCUSDT.P", "BTCUSDT"), ("btc/usdt", "BTCUSDT"), ("SOL", "SOLUSDT"),
    ("BTC-USD", "BTCUSDT"), ("ETHBTC", "ETHBTC"), ("", ""),
])
def test_normalize_symbol(raw, expected):
    assert webapp.normalize_symbol(raw) == expected


def test_ai_endpoints_without_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert client.get("/api/config").get_json()["ai"] is False
    assert client.post("/api/screenshot", json={"image": "data:image/png;base64,AAAA"}).status_code == 400
    assert client.get("/api/ai-review?demo=1").status_code == 400


def test_screenshot_with_mocked_ai(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    calls = {}
    chart = ai.ChartRead(
        symbol_guess="BTC/USDT", timeframe_guess="15m", price_on_chart=60000.0, trend="UP",
        market_structure="higher highs", patterns=["bull flag"], indicators_seen=["RSI 60"],
        supports=[59000.0], resistances=[61000.0], bias_next_period="UP", probability_up_pct=58,
        suggested_action="LONG", entry=60000.0, stop_loss=59400.0, take_profits=[61000.0],
        invalidation="close below 59000", reasoning="trend up", risks=["news"], image_quality_issues="")

    def parse(**kw):
        calls.update(kw)
        return SimpleNamespace(stop_reason="end_turn", parsed_output=chart)

    fake = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(parse=parse)))
    monkeypatch.setattr(ai, "_client", lambda: fake)
    img = "data:image/png;base64," + base64.b64encode(b"\x89PNG fake").decode()
    j = client.post("/api/screenshot", json={"image": img, "horizon": "1 hour", "demo": "1"}).get_json()
    assert j["chart"]["suggested_action"] == "LONG"
    assert j["live"]["symbol"] == "BTCUSDT" and j["live"]["timeframe"] == "15m"
    assert j["agreement"] in {"AGREE", "PARTIAL", "CONFLICT"}
    assert calls["model"] == ai.MODEL and calls["output_format"] is ai.ChartRead
    assert calls["messages"][0]["content"][0]["type"] == "image"


def test_ai_review_handles_pause_turn(monkeypatch):
    responses = iter([
        SimpleNamespace(stop_reason="pause_turn", content=[SimpleNamespace(type="text", text="**Verdict:** ")]),
        SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="CAUTION")]),
    ])
    sent = []

    def create(**kw):
        sent.append(len(kw["messages"]))
        return next(responses)

    monkeypatch.setattr(ai, "_client", lambda: SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create))))
    assert ai.review_decision({"symbol": "BTCUSDT"}) == "**Verdict:** CAUTION"
    assert sent == [1, 2]
