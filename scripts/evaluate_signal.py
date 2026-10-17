"""Evaluate whether the composite score predicts forward benchmark-relative returns.

Writes:
    docs/evaluation.md
    docs/figures/label_returns.png
    docs/figures/rolling_ic.png
    docs/figures/signal_comparison.png
and refreshes the results block in README.md.

Usage:
    python scripts/evaluate_signal.py                    # uses cached prices in data/raw
    python scripts/evaluate_signal.py --download         # fetch fresh history first
    python scripts/evaluate_signal.py --source synthetic --outdir /tmp/demo   # offline demo
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
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitor import config  # noqa: E402
from monitor.data import load, load_cache  # noqa: E402
from monitor.evaluation import EvaluationResult, evaluate  # noqa: E402

BLUE, GRAY, INK, MUTED, SURFACE = "#2a78d6", "#a8a69f", "#0b0b0b", "#52514e", "#fcfcfb"


# ------------------------------------------------------------------- formatting
def pct(x: float, signed: bool = True, digits: int = 2) -> str:
    if x is None or not np.isfinite(x):
        return "n/a"
    return f"{x * 100:{'+' if signed else ''}.{digits}f}%"


def num(x: float, digits: int = 3) -> str:
    return "n/a" if x is None or not np.isfinite(x) else f"{x:+.{digits}f}"


def ci(lo: float, hi: float, f=pct) -> str:
    return "n/a" if not (np.isfinite(lo) and np.isfinite(hi)) else f"[{f(lo)}, {f(hi)}]"


def verdict(res: EvaluationResult) -> str:
    est, lo, hi = res.ic
    if not np.isfinite(lo):
        return "There is not yet enough history to put a confidence interval on the IC."
    if lo > 0:
        return ("The 95% interval for the IC excludes zero: higher scores have been followed "
                "by higher benchmark-relative returns in this sample. The effect is small, as "
                "expected for daily equity signals, and the universe is only a handful of stocks.")
    if hi < 0:
        return ("The 95% interval for the IC is entirely below zero: in this sample, higher "
                "scores were followed by *lower* relative returns, consistent with short-term "
                "mean reversion after strong price/volume days.")
    return ("The 95% interval for the IC includes zero, so the data do not support a claim that "
            "the score predicts forward relative returns. That is a legitimate finding: the "
            "score is useful as a description of today's move, not as a forecast.")


# ---------------------------------------------------------------------- figures
def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#d6d5d0")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color="#ecebe7", linewidth=0.8)
    ax.set_axisbelow(True)


def figure_labels(res: EvaluationResult, path: Path) -> None:
    t = res.by_label.dropna(subset=["mean"])
    fig, ax = plt.subplots(figsize=(7, 3.6), facecolor=SURFACE)
    _style(ax)
    x = np.arange(len(t))
    ax.bar(x, t["mean"] * 100, width=0.55, color=BLUE, zorder=2)
    err = np.vstack([(t["mean"] - t["ci_lo"]) * 100, (t["ci_hi"] - t["mean"]) * 100])
    ax.errorbar(x, t["mean"] * 100, yerr=np.nan_to_num(err), fmt="none",
                ecolor=INK, elinewidth=1.2, capsize=4, zorder=3)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.set_xticks(x, [f"{lab}\n(n={n:,})" for lab, n in zip(t.index, t["n"])], color=INK)
    ax.set_ylabel(f"Mean {res.horizon}-day return vs SPY (%)", color=MUTED, fontsize=9)
    ax.set_title("Forward relative return by signal label, with 95% block-bootstrap CI",
                 loc="left", fontsize=10.5, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def figure_rolling(res: EvaluationResult, path: Path) -> None:
    s = res.rolling_ic
    fig, ax = plt.subplots(figsize=(7, 3.2), facecolor=SURFACE)
    _style(ax)
    if s is not None and len(s):
        ax.plot(s.index, s.values, color=BLUE, linewidth=2)
    ax.axhline(0, color=MUTED, linewidth=1)
    ax.axhline(res.ic[0], color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(1.0, res.ic[0], f" full-sample {res.ic[0]:+.3f}", transform=ax.get_yaxis_transform(),
            va="bottom", ha="right", fontsize=8.5, color=MUTED)
    ax.set_ylabel("Spearman IC", color=MUTED, fontsize=9)
    ax.set_title("Trailing 6-month information coefficient", loc="left", fontsize=10.5, color=INK)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def figure_comparison(res: EvaluationResult, path: Path) -> None:
    rows = list(res.baselines["ic"].items())
    rows += [(f"Score without {k.replace('_', ' ')}", v) for k, v in res.ablation["ic"].items()]
    if res.walk_forward:
        rows.append(("Walk-forward logistic model (out-of-sample)", res.walk_forward["ic_learned"]))
    rows = rows[::-1]
    names, vals = zip(*rows)
    fig, ax = plt.subplots(figsize=(7, 0.32 * len(rows) + 1.0), facecolor=SURFACE)
    _style(ax)
    ax.grid(axis="x", color="#ecebe7", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    colors = [BLUE if n.startswith("Composite") else GRAY for n in names]
    ax.barh(range(len(vals)), np.nan_to_num(vals), color=colors, height=0.6, zorder=2)
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.set_yticks(range(len(vals)), names, color=INK, fontsize=8.5)
    ax.set_xlabel(f"Spearman IC with {res.horizon}-day return vs SPY", color=MUTED, fontsize=9)
    ax.set_title("Composite score vs baselines and ablations", loc="left", fontsize=10.5, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------- markdown
def md_table(df: pd.DataFrame, fmt: dict) -> str:
    cols = [df.index.name or "", *df.columns]
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "|" + "|".join(["---"] + ["---:"] * len(df.columns)) + "|"]
    for idx, row in df.iterrows():
        cells = [str(idx)] + [fmt.get(c, str)(row[c]) for c in df.columns]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def summary_block(res: EvaluationResult, source: str) -> str:
    est, lo, hi = res.ic
    s_est, s_lo, s_hi = res.spread
    wf = res.walk_forward
    lines = [
        f"*Last evaluated {date.today().isoformat()} on {res.n_obs:,} ticker-days "
        f"({res.start.date()} to {res.end.date()}), {res.horizon}-day horizon, data: {source}.*",
        "",
        "| Metric | Estimate | 95% CI |",
        "|---|---:|---:|",
        f"| Rank IC: score vs forward return over SPY | {num(est)} | {ci(lo, hi, num)} |",
        f"| Rank IC, non-overlapping windows only | {num(res.ic_nonoverlap)} | |",
        f"| Mean return gap: POSITIVE-or-better minus WEAK | {pct(s_est)} | {ci(s_lo, s_hi)} |",
    ]
    if wf:
        lines.append(f"| Out-of-sample AUC: hand weights vs learned weights | "
                     f"{wf['auc_hand']:.3f} vs {wf['auc_learned']:.3f} | |")
    lines += ["", verdict(res), "", "Full write-up: [docs/evaluation.md](docs/evaluation.md)"]
    return "\n".join(lines)


def evaluation_markdown(res: EvaluationResult, source: str) -> str:
    wf = res.walk_forward
    label_fmt = {"n": lambda v: f"{int(v):,}", "mean": pct, "median": pct,
                 "hit_rate": lambda v: pct(v, signed=False, digits=1),
                 "ci_lo": pct, "ci_hi": pct}
    synthetic_note = ("\n> **These numbers come from synthetic data** and exist only to show the "
                      "pipeline works. Run on real data before drawing conclusions.\n"
                      if source != "yahoo" else "")
    wf_section = "Not enough history for a walk-forward test yet."
    if wf:
        better = wf["auc_learned"] - wf["auc_hand"]
        wf_section = (
            f"Out-of-sample period: {wf['oos_start']} onward, {wf['n_oos']:,} ticker-days.\n\n"
            "| Model | AUC (target: beats SPY) | Spearman IC |\n|---|---:|---:|\n"
            f"| Hand-weighted score | {wf['auc_hand']:.3f} | {num(wf['ic_hand'])} |\n"
            f"| Walk-forward logistic regression | {wf['auc_learned']:.3f} | {num(wf['ic_learned'])} |\n\n"
            + ("Re-learning the weights from data improves out-of-sample ranking slightly, which "
               "suggests the hand-chosen weights are not optimal."
               if better > 0.01 else
               "Learning the weights from data does not beat the hand-chosen weights out of "
               "sample. With this little data, the simpler fixed-weight model is preferable.")
        )
    return f"""# Does the score predict anything?

The daily monitor describes how well price, volume and trend line up today. This page
tests a stronger claim: **is a higher score at today's close followed by better
performance relative to the S&P 500 over the next {res.horizon} trading days?**
{synthetic_note}
## Summary

{summary_block(res, source).replace("Full write-up: [docs/evaluation.md](docs/evaluation.md)", "")}

## Setup

- **Universe:** {", ".join(res.tickers)}; benchmark {config.BENCHMARK}.
- **Sample:** {res.n_dates:,} trading days, {res.n_obs:,} ticker-days with a full score.
  Rows labelled *INSUFFICIENT DATA* (too little history, e.g. right after an IPO) are excluded.
- **Target:** {res.horizon}-day forward return minus SPY's forward return over the same days.
- **No look-ahead:** every indicator at day *t* uses data through the close of *t* only;
  this is enforced by a unit test that perturbs future prices.
- **Uncertainty:** forward windows overlap and stocks move together, so observations are not
  independent. Confidence intervals use a moving-block bootstrap that resamples 20-day blocks
  of dates, keeping both serial and cross-sectional correlation intact.

## Returns by signal label

![Forward relative return by label](figures/label_returns.png)

{md_table(res.by_label.dropna(subset=["mean"])[["n", "mean", "ci_lo", "ci_hi", "median", "hit_rate"]], label_fmt)}

## Stability

The full-sample IC can hide periods where the relationship flips sign.

![Rolling IC](figures/rolling_ic.png)

{md_table(res.by_year, {"n": lambda v: f"{int(v):,}", "ic": num})}

By ticker:

{md_table(res.by_ticker, {"n": lambda v: f"{int(v):,}", "ic": num, "first_date": str})}

## Baselines and ablation

A composite only earns its complexity if it beats its simplest ingredients. Each ablation row
re-scores the full history with one component removed and the rest re-weighted to 100.

![Signal comparison](figures/signal_comparison.png)

{md_table(res.baselines, {"ic": num})}

{md_table(res.ablation, {"ic": num, "change": num})}

A negative *change* means removing the component hurts, i.e. it was contributing.

## Hand-chosen vs learned weights

The 25/25/20/15/15 weights were set by judgement. To check whether data would choose
differently, a logistic regression on the five component scores is refit every quarter on an
expanding window and used only to score later dates. A {res.horizon}-day gap separates
each training cut-off from the test period so overlapping targets cannot leak.

{wf_section}

## Limitations

- Five stocks is a small, concentrated, highly correlated universe. Results may not
  generalise to other sectors or periods.
- Several baselines, ablations and a model are compared on the same data. Treat any single
  small difference as noise unless it holds up out of sample.
- Yahoo Finance adjusted prices; no transaction costs, no survivorship-bias control.
- A positive IC is a statistical association, not a trading strategy and not evidence of
  institutional buying.
"""


def update_readme(block: str) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(r"(<!-- EVAL:START -->\n).*?(\n<!-- EVAL:END -->)", re.S)
    if pattern.search(text):
        readme.write_text(pattern.sub(lambda m: m.group(1) + block + m.group(2), text),
                          encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tickers", nargs="+", default=config.TICKERS)
    p.add_argument("--benchmark", default=config.BENCHMARK)
    p.add_argument("--horizon", type=int, default=config.FORWARD_HORIZON)
    p.add_argument("--source", choices=["yahoo", "synthetic"], default="yahoo")
    p.add_argument("--download", action="store_true", help="refresh cached prices first")
    p.add_argument("--cache", type=Path, default=ROOT / "data" / "raw")
    p.add_argument("--outdir", type=Path, default=ROOT / "docs")
    p.add_argument("--reps", type=int, default=1000, help="bootstrap replications")
    args = p.parse_args(argv)

    symbols = list(dict.fromkeys([*args.tickers, args.benchmark]))
    if args.source == "synthetic":
        data = load(symbols, source="synthetic")
    else:
        data = load_cache(symbols, args.cache)
        if args.download or len(data) < len(symbols):
            data = load(symbols, source="yahoo", period=config.HISTORY_PERIOD, cache_dir=args.cache)

    res = evaluate(data, args.tickers, args.benchmark, args.horizon, bootstrap_reps=args.reps)

    figdir = args.outdir / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    figure_labels(res, figdir / "label_returns.png")
    figure_rolling(res, figdir / "rolling_ic.png")
    figure_comparison(res, figdir / "signal_comparison.png")
    (args.outdir / "evaluation.md").write_text(evaluation_markdown(res, args.source), encoding="utf-8")

    # Never let a synthetic demo overwrite the published README results.
    if args.source == "yahoo" and args.outdir.resolve() == (ROOT / "docs").resolve():
        update_readme(summary_block(res, args.source))

    print(summary_block(res, args.source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
