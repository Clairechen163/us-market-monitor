"""Daily end-of-session market monitor.

Usage:
    python market_monitor.py                      # live data, default universe
    python market_monitor.py --tickers NVDA AMD   # custom universe
    python market_monitor.py --source synthetic   # offline demo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from monitor import config
from monitor.data import load
from monitor.pipeline import build_panel, latest_snapshot
from monitor.report import render_text, write_reports

ROOT = Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tickers", nargs="+", default=config.TICKERS)
    p.add_argument("--benchmark", default=config.BENCHMARK)
    p.add_argument("--source", choices=["yahoo", "synthetic"], default="yahoo")
    p.add_argument("--period", default=config.HISTORY_PERIOD)
    p.add_argument("--outdir", type=Path, default=ROOT / "reports")
    p.add_argument("--cache", type=Path, default=ROOT / "data" / "raw",
                   help="where downloaded prices are cached for the evaluation")
    args = p.parse_args(argv)

    symbols = list(dict.fromkeys([*args.tickers, args.benchmark]))
    data = load(symbols, source=args.source, period=args.period,
                cache_dir=args.cache if args.source == "yahoo" else None)

    missing = [t for t in args.tickers if t not in data]
    if missing:
        print(f"WARNING: no data for {', '.join(missing)}", file=sys.stderr)
    if args.benchmark not in data:
        print(f"WARNING: benchmark {args.benchmark} unavailable; "
              "relative strength falls back to absolute returns", file=sys.stderr)

    panel = build_panel(data, args.tickers, args.benchmark)
    snapshot = latest_snapshot(panel)
    csv_path, txt_path = write_reports(snapshot, args.outdir, args.source)

    print(render_text(snapshot, args.source))
    print(f"Wrote {csv_path.relative_to(ROOT) if csv_path.is_relative_to(ROOT) else csv_path}")
    print(f"Wrote {txt_path.relative_to(ROOT) if txt_path.is_relative_to(ROOT) else txt_path}")
    return 2 if len(missing) == len(args.tickers) else 0


if __name__ == "__main__":
    raise SystemExit(main())
