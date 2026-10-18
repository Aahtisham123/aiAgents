import argparse
import sys

from . import data
from .backtest import backtest
from .odds import historical_odds
from .report import DISCLAIMER, render, render_odds
from .strategist import Strategist


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m crypto_agents",
                                description="Multi-agent crypto market analysis.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="analyze one or more symbols with live Binance data")
    a.add_argument("symbols", nargs="+", help="e.g. BTCUSDT ETHUSDT SOLUSDT")
    a.add_argument("--csv", help="use a TradingView/exchange OHLCV CSV (candles of --tf) instead of live data")
    a.add_argument("--demo", action="store_true", help="use synthetic data (offline demo)")
    a.add_argument("--tf", default="1h", choices=list(data.PROFILES), help="entry timeframe (default 1h)")
    a.add_argument("--no-odds", action="store_true", help="skip the historical win/loss odds")

    s = sub.add_parser("scan", help="rank the most traded coins (or your list) and show the best setups")
    s.add_argument("symbols", nargs="*", help="default: top coins by 24h volume")
    s.add_argument("--top", type=int, default=20)
    s.add_argument("--tf", default="1h", choices=list(data.PROFILES))

    b = sub.add_parser("backtest", help="measure the real historical win rate")
    b.add_argument("--symbol", default="BTCUSDT")
    b.add_argument("--csv", help="hourly OHLCV CSV (recommended: 1-2 years of history)")
    b.add_argument("--demo", action="store_true", help="use synthetic data")
    b.add_argument("--target-r", type=float, default=2.0)

    for sp in (a, s, b):
        sp.add_argument("--account", type=float, default=1000.0, help="account size in USDT")
        sp.add_argument("--risk", type=float, default=1.0, help="%% of account risked per trade")
    args = p.parse_args(argv)
    strat = Strategist(account_size=args.account, risk_pct=args.risk)

    if args.cmd == "analyze":
        for sym in args.symbols:
            if args.demo:
                snap = data.demo_snapshot(sym.upper(), args.tf)
            elif args.csv:
                snap = data.snapshot_from_base(sym.upper(), data.load_csv(args.csv), args.tf)
            else:
                snap = data.fetch_snapshot(sym, args.tf)
            d = strat.decide(snap)
            print(render(d))
            if not args.no_odds:
                print(render_odds(historical_odds(snap, d.score, d.action, strat)))
        return 0

    if args.cmd == "scan":
        results = []
        for sym in args.symbols or [r["symbol"] for r in data.top_symbols(args.top)]:
            try:
                results.append(strat.decide(data.fetch_snapshot(sym, args.tf)))
            except Exception as exc:  # noqa: BLE001
                print(f"{sym}: skipped ({exc})", file=sys.stderr)
        results.sort(key=lambda d: (d.action == "NO TRADE", -d.setup_quality))
        print(f"{'SYMBOL':<12}{'ACTION':<10}{'SCORE':>7}{'QUALITY':>9}{'ENTRY':>14}{'STOP':>14}{'TP1':>14}")
        for d in results:
            pl = d.plan
            print(f"{d.symbol:<12}{d.action:<10}{d.score:>+7.2f}{d.setup_quality:>9}"
                  + (f"{pl.entry:>14,.4f}{pl.stop_loss:>14,.4f}{pl.take_profits[0]:>14,.4f}" if pl else ""))
        print(f"\nRun `python -m crypto_agents analyze <SYMBOL>` for the full reasoning.\n{DISCLAIMER}")
        return 0

    hourly = data.synthetic_candles() if args.demo else data.load_csv(args.csv) if args.csv else \
        data.fetch_klines(args.symbol.upper(), "1h", 1000)
    res = backtest(hourly, args.symbol, strat, target_r=args.target_r, warmup=min(24 * 220, len(hourly) // 2))
    print("Backtest summary (R = multiples of the amount risked per trade):")
    for k, v in res.summary.items():
        print(f"  {k:<18}{v}")
    print("\nA win rate well below 100% is normal — profit comes from winners being larger than losers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
