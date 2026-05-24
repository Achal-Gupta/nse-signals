"""
Backtest CLI.

Usage:
    python backtest.py --days 90 --symbols RELIANCE.NS TCS.NS INFY.NS
    python backtest.py --days 90 --universe              # use today's universe
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.backtester import backtest_symbol, print_result
from lib.secret_validator import verify_secrets, SecretError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Backtest the NSE agent stack against historical data.")
    parser.add_argument("--days", type=int, default=90, help="Trading days of history to replay")
    parser.add_argument("--symbols", nargs="+", default=None, help="Symbols to test")
    parser.add_argument("--universe", action="store_true",
                        help="Use today's Universe Agent output as the symbol list")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.symbols and not args.universe:
        print("ERROR: provide --symbols or --universe")
        return 1

    if args.universe:
        # Universe Agent needs no secrets to compute baseline + news
        from agents.universe import build_universe
        universe = build_universe()
        symbols = [s["symbol"] for s in universe.stocks]
        print(f"Backtesting today's universe ({len(symbols)} symbols)")
    else:
        symbols = args.symbols

    all_results = []
    for sym in symbols:
        result = backtest_symbol(sym, days=args.days)
        if result is None:
            print(f"{sym}: backtest failed (no data?)")
            continue
        print_result(result)
        all_results.append(result)

    # Aggregate per-agent hit rates across all symbols
    if len(all_results) > 1:
        print("\n=== Aggregate per-agent hit rate ===")
        from collections import defaultdict
        sums = defaultdict(list)
        for r in all_results:
            for agent, rate in r.per_agent_hit_rate.items():
                if rate > 0:
                    sums[agent].append(rate)
        for agent, rates in sums.items():
            avg = sum(rates) / len(rates) if rates else 0
            print(f"  {agent:12s} {avg:5.1f}%  (across {len(rates)} symbols)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
