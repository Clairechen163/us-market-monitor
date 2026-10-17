"""Daily text + CSV report."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import WEIGHTS
from .scoring import COMPONENTS

REPORT_COLUMNS = [
    "date", "Close", "ret_1d", "ret_5d", "ret_20d", "excess_5d", "excess_20d",
    "rvol20", "ema20", "ema50", "ema200", "rsi14", "atr14_pct", "prior_high20",
    "breakout_pct", *[f"pts_{c}" for c in COMPONENTS], "coverage", "score", "label",
]


def _pct(x: float) -> str:
    return "n/a" if not np.isfinite(x) else f"{x * 100:+.1f}%"


def _num(x: float, fmt: str = "{:.2f}") -> str:
    return "n/a" if not np.isfinite(x) else fmt.format(x)


def snapshot_table(snapshot: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in REPORT_COLUMNS if c in snapshot.columns]
    return snapshot[cols].sort_values("score", ascending=False, na_position="last")


def render_text(snapshot: pd.DataFrame, source: str) -> str:
    snap = snapshot_table(snapshot)
    as_of = pd.to_datetime(snap["date"]).max().date()
    lines = [
        "US MARKET MONITOR",
        f"Session: {as_of}   Data source: {source}",
        "Signals describe price/volume alignment. They are not buy/sell recommendations.",
        "",
    ]
    for ticker, r in snap.iterrows():
        lines += [
            f"{ticker:<6} score {_num(r['score'], '{:.1f}'):>5}  [{r['label']}]  "
            f"(coverage {r['coverage']:.0%})",
            f"   close {_num(r['Close'])}  1d {_pct(r['ret_1d'])}  5d {_pct(r['ret_5d'])}  "
            f"20d {_pct(r['ret_20d'])}  5d vs SPY {_pct(r['excess_5d'])}",
            f"   RVOL20 {_num(r['rvol20'])}  RSI14 {_num(r['rsi14'], '{:.1f}')}  "
            f"ATR14 {_pct(r['atr14_pct'])}  vs prior 20d high {_pct(r['breakout_pct'])}",
            "   components: "
            + "  ".join(
                f"{c} {_num(r[f'pts_{c}'], '{:.1f}')}/{WEIGHTS[c]:.0f}" for c in COMPONENTS
            ),
            "",
        ]
    return "\n".join(lines)


def write_reports(snapshot: pd.DataFrame, outdir: Path, source: str) -> tuple[Path, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    snap = snapshot_table(snapshot)
    stamp = pd.to_datetime(snap["date"]).max().strftime("%Y%m%d")
    suffix = "" if source == "yahoo" else f"_{source}"
    csv_path = outdir / f"market_report_{stamp}{suffix}.csv"
    txt_path = outdir / f"market_report_{stamp}{suffix}.txt"
    snap.to_csv(csv_path, index_label="ticker", float_format="%.6g")
    txt_path.write_text(render_text(snapshot, source), encoding="utf-8")
    return csv_path, txt_path
