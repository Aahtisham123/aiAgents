from .strategist import Decision

DISCLAIMER = ("NOT FINANCIAL ADVICE. No signal is 100% accurate — every trade can lose. "
              "Always use the stop-loss and never risk money you cannot afford to lose.")


def _fmt(x: float) -> str:
    return f"{x:,.2f}" if x >= 1 else f"{x:.6f}"


def render(d: Decision) -> str:
    out = ["=" * 72, f"  {d.symbol} — MULTI-AGENT ANALYSIS", "=" * 72]
    for r in d.reports:
        bias = "" if r.agent == "Risk Manager" else f" [{r.bias} {r.score:+.2f}]"
        out.append(f"\n▶ {r.agent}{bias} (confidence {r.confidence:.0%})")
        out.append(f"  {r.summary}")
        out += [f"   • {x}" for x in r.reasons]

    out += ["", "-" * 72, f"  CHIEF STRATEGIST DECISION:  {d.action}", "-" * 72]
    out.append(f"  Combined score: {d.score:+.2f}   Setup quality: {d.setup_quality}/100 "
               f"(checklist score, not a win probability)")
    out += [f"  - {x}" for x in d.reasons]
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
