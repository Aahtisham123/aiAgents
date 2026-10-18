"""Web app / Vercel entrypoint: JSON API + a browser UI for the multi-agent analysis."""
from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

import numpy as np
from flask import Flask, Response, jsonify, request

from crypto_agents import Strategist, data
from crypto_agents.report import DISCLAIMER
from crypto_agents.web_page import PAGE

app = Flask(__name__)

DEFAULT_SCAN = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
                "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT"]


def _clean(x):
    """Make agent output JSON-safe (numpy types, NaN/inf)."""
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, np.generic):
        x = x.item()
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def _strategist() -> Strategist:
    account = min(max(float(request.args.get("account", 1000)), 1), 1e9)
    risk = min(max(float(request.args.get("risk", 1)), 0.05), 10)
    return Strategist(account_size=account, risk_pct=risk)


def _snapshot(symbol: str, demo: bool):
    if demo:
        return data.snapshot_from_hourly(symbol, data.synthetic_candles())
    return data.fetch_snapshot(symbol)


def _decision_json(d) -> dict:
    out = asdict(d)
    for r, rep in zip(out["reports"], d.reports):
        r["bias"] = rep.bias
    out["disclaimer"] = DISCLAIMER
    return _clean(out)


@app.get("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/analyze")
def analyze():
    symbol = request.args.get("symbol", "BTCUSDT").strip().upper()
    demo = request.args.get("demo") in ("1", "true")
    try:
        d = _strategist().decide(_snapshot(symbol, demo))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except Exception as exc:  # noqa: BLE001
        return jsonify(error=f"Market data unavailable: {exc}"), 502
    return jsonify(_decision_json(d))


@app.get("/api/scan")
def scan():
    raw = request.args.get("symbols", "")
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()][:15] or DEFAULT_SCAN
    demo = request.args.get("demo") in ("1", "true")
    strat = _strategist()

    def run(sym):
        try:
            d = strat.decide(_snapshot(sym, demo))
            p = d.plan
            return {"symbol": sym, "action": d.action, "score": d.score, "setup_quality": d.setup_quality,
                    "entry": p.entry if p else None, "stop_loss": p.stop_loss if p else None,
                    "take_profit_1": p.take_profits[0] if p else None}
        except Exception as exc:  # noqa: BLE001
            return {"symbol": sym, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(run, symbols))
    results.sort(key=lambda r: ("error" in r, r.get("action") == "NO TRADE", -r.get("setup_quality", 0)))
    return jsonify(_clean({"results": results, "disclaimer": DISCLAIMER}))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
