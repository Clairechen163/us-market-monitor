"""Evaluate whether the pre-market score predicts the open-to-close return vs SPY.

Writes docs/premarket_evaluation.md, docs/figures/premarket_label_returns.png
and refreshes the pre-market results block in README.md.

Usage:
    python scripts/evaluate_premarket.py --download      # ~2 years of hourly extended-hours bars
    python scripts/evaluate_premarket.py --source synthetic --outdir /tmp/demo
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(HERE)]

from evaluate_signal import INK, MUTED, SURFACE, _style, ci, label_bars, md_table, num, pct  # noqa: E402
from monitor import config  # noqa: E402
from monitor import intraday as intr  # noqa: E402
from monitor.data import load as load_daily, load_cache as load_daily_cache  # noqa: E402
from monitor.premarket_eval import PremarketResult, evaluate_premarket  # noqa: E402

from premarket_monitor import parse_hhmm  # noqa: E402


def verdict(res: PremarketResult) -> str:
    est, lo, hi = res.ic
    if not np.isfinite(lo):
        return "Not enough history yet to put a confidence interval on the IC."
    if lo > 0:
        return ("The 95% interval excludes zero: stocks with higher pre-market scores have gone on to "
                "beat SPY from the open to the close more often than lower-scored ones in this sample.")
    if hi < 0:
        return ("The 95% interval is entirely below zero: strong pre-market setups have tended to "
                "*underperform* SPY after the open, consistent with gaps fading during the session.")
    return ("The 95% interval includes zero, so the data do not show that the pre-market score "
            "predicts the regular session. It describes the pre-market well; it is not a forecast.")


def summary_block(res: PremarketResult, source: str) -> str:
    est, lo, hi = res.ic
    s, s_lo, s_hi = res.spread
    gap_ic = res.baselines.loc["Gap vs SPY only", "ic"]
    return "\n".join([
        f"*Last evaluated {date.today().isoformat()} on {res.n_obs:,} ticker-days "
        f"({res.start.date()} to {res.end.date()}), pre-market bars through "
        f"{res.cutoff.strftime('%H:%M')} ET, data: {source}.*",
        "",
        "| Metric | Estimate | 95% CI |",
        "|---|---:|---:|",
        f"| Rank IC: pre-market score vs open-to-close return over SPY | {num(est)} | {ci(lo, hi, num)} |",
        f"| Mean return gap: POSITIVE-or-better minus WEAK | {pct(s)} | {ci(s_lo, s_hi)} |",
        f"| Rank IC: gap vs SPY alone (negative = gaps fade) | {num(gap_ic)} | |",
        "",
        verdict(res),
        "",
        "Full write-up: [docs/premarket_evaluation.md](docs/premarket_evaluation.md)",
    ])


def figure_labels(res: PremarketResult, path: Path) -> None:
    t = res.by_label.dropna(subset=["mean"])
    fig, ax = plt.subplots(figsize=(7, 3.6), facecolor=SURFACE)
    _style(ax)
    label_bars(ax, t)
    ax.set_ylabel("Mean open-to-close return vs SPY (%)", color=MUTED, fontsize=9)
    ax.set_title("Regular-session relative return by pre-market label, 95% block-bootstrap CI",
                 loc="left", fontsize=10.5, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def evaluation_markdown(res: PremarketResult, source: str) -> str:
    label_fmt = {"n": lambda v: f"{int(v):,}", "mean": pct, "median": pct,
                 "hit_rate": lambda v: pct(v, signed=False, digits=1), "ci_lo": pct, "ci_hi": pct}
    demo = ("\n> **These numbers come from synthetic data** and only show that the pipeline runs.\n"
            if source != "yahoo" else "")
    summary = summary_block(res, source).replace(
        "Full write-up: [docs/premarket_evaluation.md](docs/premarket_evaluation.md)", "")
    return f"""# Does the pre-market score predict the regular session?

The [pre-market snapshot](premarket.md) describes how each stock is trading before the open.
This page tests whether that description carries information about what happens next:
**is a higher pre-market score followed by a better return from the 09:30 open to the 16:00
close, relative to SPY over the same hours?**
{demo}
## Summary

{summary}
## Setup

- **Universe:** {", ".join(res.tickers)}; benchmark {config.BENCHMARK}.
- **Sample:** {res.n_dates:,} trading days, {res.n_obs:,} ticker-days with a full pre-market score.
  {res.n_dropped_gaps:,} ticker-days with a gap larger than {config.MAX_PLAUSIBLE_GAP:.0%} were dropped as
  likely data errors or corporate actions.
- **Snapshot time:** pre-market bars that closed by {res.cutoff.strftime('%H:%M')} ET. Yahoo keeps
  extended-hours history only at hourly resolution beyond ~60 days, so the evaluation uses hourly
  bars; the live monitor uses 5-minute bars and runs at ~08:40 ET.
- **Target:** open-to-close return minus SPY's open-to-close return. It begins after every input is
  known, so there is no look-ahead. Daily context comes from the previous completed session.
- **Uncertainty:** one-day targets do not overlap, but stocks move together within a day, so
  intervals come from a block bootstrap over dates.

## Returns by pre-market label

![Open-to-close relative return by pre-market label](figures/premarket_label_returns.png)

{md_table(res.by_label.dropna(subset=["mean"])[["n", "mean", "ci_lo", "ci_hi", "median", "hit_rate"]], label_fmt)}

## Baselines

{md_table(res.baselines, {"ic": num})}

The gap rows answer a classic market-microstructure question directly: a negative IC means
pre-market moves have tended to reverse after the open (gap fade); a positive IC means they
have tended to extend (gap continuation).

## Ablation

{md_table(res.ablation, {"ic": num, "change": num})}

A negative *change* means removing the component lowers the IC, i.e. it was contributing.

## By ticker

{md_table(res.by_ticker, {"n": lambda v: f"{int(v):,}", "ic": num, "mean_gap_abs": lambda v: pct(v, signed=False)})}

## Limitations

- About two years of hourly extended-hours data from Yahoo Finance, an unofficial source.
  Extended-hours volume is sometimes missing; when it is, the volume component is left out and
  the score re-normalised (see *coverage*).
- Intraday prices are not dividend-adjusted; on ex-dividend days the measured gap includes the
  dividend. The effect is small for this universe.
- Open-to-close returns ignore the cost of trading at the open, when spreads are widest.
- {len(res.tickers)} correlated stocks; several comparisons on the same data. Not investment advice.
"""


def update_readme(block: str) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(r"(<!-- PREMARKET-EVAL:START -->\n).*?(\n<!-- PREMARKET-EVAL:END -->)", re.S)
    if pattern.search(text):
        readme.write_text(pattern.sub(lambda m: m.group(1) + block + m.group(2), text), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tickers", nargs="+", default=config.TICKERS)
    p.add_argument("--benchmark", default=config.BENCHMARK)
    p.add_argument("--cutoff", type=parse_hhmm, default=parse_hhmm("09:00"),
                   help="use pre-market bars that closed by this ET time (default 09:00)")
    p.add_argument("--source", choices=["yahoo", "synthetic"], default="yahoo")
    p.add_argument("--download", action="store_true")
    p.add_argument("--cache", type=Path, default=ROOT / "data" / "raw")
    p.add_argument("--outdir", type=Path, default=ROOT / "docs")
    p.add_argument("--reps", type=int, default=1000)
    args = p.parse_args(argv)

    symbols = list(dict.fromkeys([*args.tickers, args.benchmark]))
    if args.source == "synthetic":
        intraday = intr.load_synthetic_intraday(symbols, n_days=300, interval_minutes=60)
        daily = intr.daily_from_intraday(intraday)
    else:
        icache = args.cache / "intraday_1h"
        intraday = intr.load_cache(symbols, icache)
        if args.download or len(intraday) < len(symbols):
            intraday = intr.load_yahoo_intraday(symbols, period="720d", interval="1h")
            intr.save_cache(intraday, icache)
        daily = load_daily_cache(symbols, args.cache)
        if len(daily) < len(symbols):
            daily = load_daily(symbols, source="yahoo", period=config.HISTORY_PERIOD, cache_dir=args.cache)

    res = evaluate_premarket(intraday, daily, args.tickers, args.benchmark, args.cutoff, reps=args.reps)

    (args.outdir / "figures").mkdir(parents=True, exist_ok=True)
    figure_labels(res, args.outdir / "figures" / "premarket_label_returns.png")
    (args.outdir / "premarket_evaluation.md").write_text(evaluation_markdown(res, args.source), encoding="utf-8")
    if args.source == "yahoo" and args.outdir.resolve() == (ROOT / "docs").resolve():
        update_readme(summary_block(res, args.source))
    print(summary_block(res, args.source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
