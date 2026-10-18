from .strategist import Decision

DISCLAIMER = ("NOT FINANCIAL ADVICE. No signal is 100% accurate — every trade can lose. "
              "Always use the stop-loss and never risk money you cannot afford to lose.")


def _fmt(x: float) -> str:
    return f"{x:,.2f}" if x >= 1 else f"{x:.6f}"


def render(d: Decision) -> str:
    out = ["=" * 72, f"  {d.symbol} {d.timeframe} — MULTI-AGENT ANALYSIS (price {_fmt(d.price)})", "=" * 72]
    for r in d.reports:
        bias = "" if r.agent == "Risk Manager" else f" [{r.bias} {r.score:+.2f}]"
        out.append(f"\n▶ {r.agent}{bias} (confidence {r.confidence:.0%})")
        out.append(f"  {r.summary}")
        out += [f"   • {x}" for x in r.reasons]

    out += ["", "-" * 72, f"  CHIEF STRATEGIST DECISION:  {d.action}", "-" * 72]
    out.append(f"  Combined score: {d.score:+.2f}   Setup quality: {d.setup_quality}/100 "
               f"(checklist score, not a win probability)")
    out += [f"  - {x}" for x in d.reasons]
    out += [f"  Strategy: {d.strategy} — {d.playbook}", f"  Signal valid for: {d.horizon_text}"]
    if d.plan:
        p = d.plan
        out += [
            "",
            f"  Entry        : {_fmt(p.entry)}",
            f"  Stop-loss    : {_fmt(p.stop_loss)}  ({abs(p.entry - p.stop_loss) / p.entry * 100:.2f}% away)",
        ]
        for n, (tp, rr) in enumerate(zip(p.take_profits, (1.5, 2.5, 4.0)), 1):
            out.append(f"  Take-profit {n}: {_fmt(tp)}  ({rr}R)")
        out += [
            f"  Position size: {p.position_size:.6f} units ≈ {p.position_value:,.2f} USDT "
            f"(≈{p.leverage_needed:.1f}x of account)",
            f"  Max loss     : {p.risk_amount:,.2f} USDT if the stop is hit",
            "  Management   : take partial profit at TP1 and move the stop to break-even.",
        ]
    if d.warnings:
        out += ["", "  Warnings:"] + [f"  ! {w}" for w in d.warnings]
    out += ["", f"  {DISCLAIMER}", "=" * 72]
    return "\n".join(out)


def render_odds(o: dict) -> str:
    if "error" in o:
        return f"  Odds: {o['error']}"

    def line(label, x):
        if not x or not x["signals"]:
            return f"  {label}: no signals"
        lo, hi = x["win_rate_95ci"]
        return (f"  {label}: {x['win_rate']:.0%} won ({x['wins']}W/{x['losses']}L/{x['timeouts']} expired "
                f"of {x['signals']}; 95% range {lo:.0%}-{hi:.0%}; avg {x['avg_r']:+.2f}R)")

    out = ["", "  MEASURED ODDS (recent history of this coin & timeframe)",
           f"  Chance price is higher after {o['horizon_candles']} candles: {o['chance_up']:.0%} "
           f"(from {o['chance_samples']} moments with {o['chance_basis']}; normal up-rate {o['base_rate_up']:.0%})"]
    if o.get("same_direction"):
        out.append(line("Past signals in this direction", o["same_direction"]))
    out.append(line("All past signals", o["all_signals"]))
    out.append(f"  Win = {o['target']}. Period: {o['period']}. {o['note']}")
    return "\n".join(out)


def render_forecast(f: dict) -> str:
    from datetime import datetime, timezone
    if "error" in f:
        return f"  Forecast: {f['error']}"
    t0 = datetime.fromtimestamp(f["target_candle_open"], timezone.utc).strftime("%H:%M")
    t1 = datetime.fromtimestamp(f["target_candle_close"], timezone.utc).strftime("%H:%M")
    t = f["model_test"]
    out = ["=" * 72, f"  NEXT {f['timeframe']} CANDLE {t0}-{t1} UTC · {f['symbol']} @ {_fmt(f['price'])}",
           f"  >>> {f['action']} <<<   UP {f['probability_up']:.0%} / DOWN {f['probability_down']:.0%}"]
    if t.get("calls"):
        lo, hi = t["call_accuracy_95ci"]
        out.append(f"  Model on recent unseen candles: {t['call_accuracy']:.0%} right on {t['calls']} calls "
                   f"(95% range {lo:.0%}-{hi:.0%}; always-guess-majority = {t['majority_baseline']:.0%}) "
                   f"-> {'EDGE' if f['has_edge'] else 'NO PROVEN EDGE'}")
    out += [f"  - {r}" for r in f["reasons"]] + [f"  ! {v}" for v in f["vetoes"]]
    out.append("  Drivers: " + ", ".join(f"{d['feature']} → {d['push']}" for d in f["drivers"]))
    if f["plan"]:
        p = f["plan"]
        out.append(f"  Entry {_fmt(p['entry'])} · stop {_fmt(p['stop_loss'])} · target {_fmt(p['take_profit'])} · {p['exit']}")
    out.append(f"  {DISCLAIMER}")
    return "\n".join(out)
