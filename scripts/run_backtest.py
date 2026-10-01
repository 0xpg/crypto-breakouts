from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from engine import Config, backtest, summary  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the binary breakout ensemble")
    parser.add_argument("panel", type=Path, help="CSV: date,symbol,open,close[,eligible]")
    parser.add_argument("--output", type=Path, default=PROJECT / "results" / "daily.csv")
    parser.add_argument("--lookbacks", type=int, nargs="+", default=[10, 20, 40, 80])
    parser.add_argument("--max-age", type=int, default=5)
    parser.add_argument("--max-weight", type=float, default=0.025)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    args = parser.parse_args()

    raw = pd.read_csv(args.panel, parse_dates=["date"])
    required = {"date", "symbol", "open", "close"}
    if missing := required - set(raw.columns):
        parser.error(f"missing columns: {', '.join(sorted(missing))}")
    opens = raw.pivot(index="date", columns="symbol", values="open").sort_index()
    closes = raw.pivot(index="date", columns="symbol", values="close").reindex_like(opens)
    eligible = None
    if "eligible" in raw:
        eligible = raw.pivot(index="date", columns="symbol", values="eligible").reindex_like(opens).fillna(False).astype(bool)

    config = Config(
        lookbacks=tuple(args.lookbacks),
        max_age=args.max_age,
        max_weight=args.max_weight,
        cost_bps=args.cost_bps,
        initial_equity=args.initial_equity,
    )
    result = backtest(opens, closes, eligible, config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output)
    print(json.dumps(summary(result), indent=2))


if __name__ == "__main__":
    main()
