"""Glue: raw OHLCV -> indicators -> scores, for one ticker or a universe."""

from __future__ import annotations

import pandas as pd

from .indicators import add_indicators
from .scoring import score_frame


def build_panel(
    data: dict[str, pd.DataFrame],
    tickers: list[str],
    benchmark: str | None,
    exclude: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Long panel (date, ticker) with indicators and scores for every day."""
    bench_close = data[benchmark]["Close"] if benchmark and benchmark in data else None
    frames = []
    for t in tickers:
        if t not in data:
            continue
        ind = add_indicators(data[t], bench_close)
        scored = ind.join(score_frame(ind, exclude=exclude))
        scored["ticker"] = t
        frames.append(scored)
    if not frames:
        raise RuntimeError("no data for any ticker")
    panel = pd.concat(frames)
    panel.index.name = "date"
    return panel.reset_index().set_index(["date", "ticker"]).sort_index()


def latest_snapshot(panel: pd.DataFrame) -> pd.DataFrame:
    """Most recent row per ticker."""
    snap = panel.reset_index().sort_values("date").groupby("ticker").tail(1)
    return snap.set_index("ticker")
