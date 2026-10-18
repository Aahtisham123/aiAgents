"""Web app / Vercel entrypoint: JSON API + browser UI for the multi-agent analysis."""
from __future__ import annotations

import base64
import binascii
import math
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

import numpy as np
from flask import Flask, Response, jsonify, request

from crypto_agents import Strategist, ai, data
from crypto_agents.odds import historical_odds
from crypto_agents.report import DISCLAIMER
from crypto_agents.web_page import PAGE

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024  # screenshots are resized in the browser first


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


def _args(src=None) -> dict:
    src = src if src is not None else request.args
    tf = str(src.get("tf", "1h"))
    if tf not in data.PROFILES:
        raise ValueError(f"Unsupported timeframe {tf!r}. Use one of {', '.join(data.PROFILES)}")
    return {
        "symbol": normalize_symbol(str(src.get("symbol", "BTCUSDT"))) or "BTCUSDT",
        "tf": tf,
        "demo": str(src.get("demo", "")).lower() in ("1", "true"),
        "account": min(max(float(src.get("account", 1000)), 1), 1e9),
        "risk": min(max(float(src.get("risk", 1)), 0.05), 10),
    }


def normalize_symbol(raw: str) -> str:
    """'BINANCE:BTCUSDT.P', 'btc/usdt', 'BTC-USD' -> 'BTCUSDT'."""
    s = raw.strip().upper().split(":")[-1].split(".")[0]
    s = re.sub(r"[^A-Z0-9]", "", s)
    if s.endswith("PERP"):
        s = s[:-4]
    if s.endswith("USD"):
        s += "T"
    if s and not s.endswith(("USDT", "USDC", "BTC", "ETH", "BNB", "FDUSD")):
        s += "USDT"
    return s


def _snapshot(a: dict, orderflow: bool = True):
    if a["demo"]:
        return data.demo_snapshot(a["symbol"], a["tf"])
    return data.fetch_snapshot(a["symbol"], a["tf"], orderflow=orderflow)


def _decision_json(d) -> dict:
    out = asdict(d)
    for r, rep in zip(out["reports"], d.reports):
        r["bias"] = rep.bias
    out["disclaimer"] = DISCLAIMER
    return _clean(out)


def _errors(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        except ConnectionError as exc:
            return jsonify(error=f"Market data unavailable: {exc}"), 502
        except Exception as exc:  # noqa: BLE001
            return jsonify(error=f"{exc.__class__.__name__}: {exc}"), 500
    wrapper.__name__ = fn.__name__
    return wrapper


@app.get("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/config")
def config():
    return jsonify(ai=ai.available(), model=ai.MODEL if ai.available() else None,
                   timeframes=list(data.PROFILES))


@app.get("/api/analyze")
@_errors
def analyze():
    a = _args()
    d = Strategist(a["account"], a["risk"]).decide(_snapshot(a))
    return jsonify(_decision_json(d))


@app.get("/api/odds")
@_errors
def odds():
    a = _args()
    snap = _snapshot(a, orderflow=False)
    strat = Strategist(a["account"], a["risk"])
    d = strat.decide(snap)
    return jsonify(_clean(historical_odds(snap, d.score, d.action, strat)))


@app.get("/api/scan")
@_errors
def scan():
    a = _args()
    raw = request.args.get("symbols", "")
    if raw.strip():
        universe = [{"symbol": normalize_symbol(s)} for s in raw.split(",") if s.strip()][:40]
    elif a["demo"]:
        universe = [{"symbol": s} for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")]
    else:
        universe = data.top_symbols(min(max(int(request.args.get("top", 20)), 1), 40))
    strat = Strategist(a["account"], a["risk"])

    def run(row):
        try:
            d = strat.decide(_snapshot({**a, "symbol": row["symbol"]}))
            p = d.plan
            return {**row, "action": d.action, "score": d.score, "setup_quality": d.setup_quality,
                    "strategy": d.strategy, "price": d.price,
                    "entry": p.entry if p else None, "stop_loss": p.stop_loss if p else None,
                    "take_profit_1": p.take_profits[0] if p else None}
        except Exception as exc:  # noqa: BLE001
            return {**row, "error": str(exc)}

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(run, universe))
    results.sort(key=lambda r: ("error" in r, r.get("action") == "NO TRADE", -r.get("setup_quality", 0)))
    return jsonify(_clean({"timeframe": a["tf"], "results": results, "disclaimer": DISCLAIMER}))


@app.get("/api/ai-review")
@_errors
def ai_review():
    if not ai.available():
        return jsonify(error="AI is not configured. Add ANTHROPIC_API_KEY in your Vercel environment variables."), 400
    a = _args()
    snap = _snapshot(a)
    strat = Strategist(a["account"], a["risk"])
    d = strat.decide(snap)
    dj = _decision_json(d)
    return jsonify({"decision": dj, "review": ai.review_decision(dj)})


@app.post("/api/screenshot")
@_errors
def screenshot():
    if not ai.available():
        return jsonify(error="Screenshot analysis needs AI. Add ANTHROPIC_API_KEY in your Vercel environment variables."), 400
    body = request.get_json(force=True, silent=True) or {}
    m = re.match(r"data:(image/(?:png|jpeg|webp|gif));base64,(.+)", body.get("image", ""), re.S)
    if not m:
        raise ValueError("Send the screenshot as a PNG/JPEG/WEBP data URL in the 'image' field")
    media_type, b64 = m.group(1), m.group(2)
    try:
        base64.b64decode(b64, validate=True)
    except binascii.Error as exc:
        raise ValueError("Image data is not valid base64") from exc

    tf = str(body.get("tf", ""))
    horizon = str(body.get("horizon", ""))
    chart = ai.analyze_screenshot(b64, media_type, tf, horizon, str(body.get("note", ""))[:500])
    result = {"chart": chart.model_dump(), "live": None, "live_error": None, "agreement": None}

    # Cross-check the picture against live data for the same coin and timeframe.
    symbol = normalize_symbol(str(body.get("symbol") or chart.symbol_guess))
    live_tf = tf if tf in data.PROFILES else chart.timeframe_guess if chart.timeframe_guess in data.PROFILES else "1h"
    if symbol:
        try:
            a = _args({**body, "symbol": symbol, "tf": live_tf})
            d = Strategist(a["account"], a["risk"]).decide(_snapshot(a))
            result["live"] = _decision_json(d)
            live_action = d.action if d.action != "NO TRADE" else "WAIT"
            result["agreement"] = ("AGREE" if live_action == chart.suggested_action else
                                   "PARTIAL" if "WAIT" in (live_action, chart.suggested_action) else "CONFLICT")
        except Exception as exc:  # noqa: BLE001
            result["live_error"] = f"Live cross-check for {symbol} failed: {exc}"
    return jsonify(_clean(result))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
