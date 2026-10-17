"""Turn the latest market report CSV into README badges and docs/dashboard.md.

Usage:
    python scripts/update_dashboard.py                  # newest reports/market_report_*.csv
    python scripts/update_dashboard.py --csv path.csv --outdir /tmp/preview
"""

from __future__ import annotations

import argparse
import sys
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitor import config  # noqa: E402
from monitor.scoring import COMPONENTS  # noqa: E402

LABEL_COLORS = {
    "STRONG PRICE/VOLUME": "#0b7d0b",
    "POSITIVE": "#2a78d6",
    "WATCH": "#b7790b",
    "WEAK": "#c03636",
    config.INSUFFICIENT_LABEL: "#6b6a65",
}
SHORT = {"STRONG PRICE/VOLUME": "STRONG", config.INSUFFICIENT_LABEL: "NO DATA"}


def _text_width(s: str) -> int:
    # Approximate Verdana 11px advance widths, as used by shields.io.
    return int(sum(7.5 if c.isupper() or c.isdigit() else 6.2 if c != " " else 3.6 for c in s)) + 10


def badge_svg(left: str, right: str, color: str) -> str:
    lw, rw = _text_width(left), _text_width(right)
    w = lw + rw
    left, right = escape(left), escape(right)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{left}: {right}">
<title>{left}: {right}</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#3d3d3a"/><rect x="{lw}" width="{rw}" height="20" fill="{color}"/><rect width="{w}" height="20" fill="url(#s)"/></g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
<text x="{lw / 2}" y="14">{left}</text><text x="{lw + rw / 2}" y="14">{right}</text></g>
</svg>
"""


def latest_csv(reports: Path) -> Path:
    files = sorted(p for p in reports.glob("market_report_*.csv") if "synthetic" not in p.name)
    if not files:
        raise SystemExit(f"no market_report_*.csv in {reports}; run market_monitor.py first")
    return files[-1]


def fmt_pct(x) -> str:
    return "–" if pd.isna(x) else f"{x * 100:+.1f}%"


def fmt_num(x, f="{:.2f}") -> str:
    return "–" if pd.isna(x) else f.format(x)


def dashboard_md(df: pd.DataFrame, csv_name: str) -> str:
    as_of = pd.to_datetime(df["date"]).max().date()
    rows = [
        "| Ticker | Badge | Score | Close | 1d | 5d vs SPY | RVOL20 | RSI14 | vs 20d high | ATR % |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for t, r in df.iterrows():
        rows.append(
            f"| **{t}** | ![{t}](badges/{t}.svg) | {fmt_num(r['score'], '{:.1f}')} | "
            f"{fmt_num(r['Close'])} | {fmt_pct(r['ret_1d'])} | {fmt_pct(r['excess_5d'])} | "
            f"{fmt_num(r['rvol20'])} | {fmt_num(r['rsi14'], '{:.1f}')} | "
            f"{fmt_pct(r['breakout_pct'])} | {fmt_pct(r['atr14_pct'])} |"
        )

    comp = ["| Ticker | " + " | ".join(f"{c.replace('_', ' ').title()} (/{config.WEIGHTS[c]:.0f})"
                                         for c in COMPONENTS) + " | Coverage |",
            "|---|" + "---:|" * (len(COMPONENTS) + 1)]
    for t, r in df.iterrows():
        comp.append(f"| {t} | " + " | ".join(fmt_num(r[f'pts_{c}'], '{:.1f}') for c in COMPONENTS)
                    + f" | {r['coverage']:.0%} |")

    return f"""# Dashboard

**Session:** {as_of} · **Source file:** `reports/{csv_name}` · regenerated automatically after each U.S. close.

> Signals describe how well today's price, volume and trend line up. They are not
> buy/sell recommendations and not evidence of institutional activity. Whether they
> carry any forward-looking information is tested separately in [evaluation.md](evaluation.md).

## Latest signals

{chr(10).join(rows)}

## Score breakdown

Points earned per component. When an input is unavailable (for example no 200-day EMA yet
after an IPO), that part is left out and the score is re-normalised; *Coverage* shows the share
of the 100 points that could be computed. Below {config.MIN_COVERAGE:.0%} the label is
*{config.INSUFFICIENT_LABEL}*.

{chr(10).join(comp)}

## Label scale

| Label | Score |
|---|---|
| STRONG PRICE/VOLUME | 75–100 |
| POSITIVE | 60–74.9 |
| WATCH | 45–59.9 |
| WEAK | below 45 |
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", type=Path)
    p.add_argument("--reports", type=Path, default=ROOT / "reports")
    p.add_argument("--outdir", type=Path, default=ROOT / "docs")
    args = p.parse_args(argv)

    csv = args.csv or latest_csv(args.reports)
    df = pd.read_csv(csv, index_col="ticker").sort_values("score", ascending=False, na_position="last")

    badges = args.outdir / "badges"
    badges.mkdir(parents=True, exist_ok=True)
    for t, r in df.iterrows():
        label = r["label"]
        right = (f"{SHORT.get(label, label)} {r['score']:.0f}"
                 if np.isfinite(r["score"]) and label != config.INSUFFICIENT_LABEL else SHORT.get(label, label))
        (badges / f"{t}.svg").write_text(badge_svg(t, right, LABEL_COLORS.get(label, "#6b6a65")),
                                          encoding="utf-8")

    (args.outdir / "dashboard.md").write_text(dashboard_md(df, csv.name), encoding="utf-8")
    print(f"Updated {len(df)} badges and dashboard from {csv.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
