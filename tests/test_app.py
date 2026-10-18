from app import app


def test_analyze_demo():
    r = app.test_client().get("/api/analyze?symbol=btcusdt&demo=1&account=500&risk=2")
    assert r.status_code == 200
    j = r.get_json()
    assert j["symbol"] == "BTCUSDT" and j["action"] in {"LONG", "SHORT", "NO TRADE"}
    assert len(j["reports"]) == 5 and "bias" in j["reports"][0]


def test_scan_demo_and_index():
    c = app.test_client()
    j = c.get("/api/scan?symbols=AAAUSDT,BBBUSDT&demo=1").get_json()
    assert [r["symbol"] for r in j["results"]] and all("action" in r for r in j["results"])
    assert b"Crypto Trading Agents" in c.get("/").data
