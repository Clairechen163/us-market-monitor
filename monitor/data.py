"""Market-data loading.

Two sources:
* ``yahoo``     – daily OHLCV from Yahoo Finance via yfinance (default).
* ``synthetic`` – reproducible simulated prices for tests, CI and offline
                  demos. Synthetic output is always labelled as such and is
                  never written into the published dashboard.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def _normalise(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame[OHLCV].copy()
    frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    frame = frame.dropna(subset=["Close"])
    return frame.astype(float)


def load_yahoo(tickers: list[str], period: str = "5y") -> dict[str, pd.DataFrame]:
    """Download split/dividend-adjusted daily bars. Missing symbols are skipped."""
    import yfinance as yf

    raw = yf.download(
        tickers=tickers,
        period=period,
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    out: dict[str, pd.DataFrame] = {}
    for t in tickers:
        try:
            frame = raw[t] if isinstance(raw.columns, pd.MultiIndex) else raw
        except KeyError:
            continue
        frame = _normalise(frame)
        if not frame.empty:
            out[t] = frame
    return out


def load_synthetic(
    tickers: list[str], n_days: int = 1000, seed: int = 7, end: str | None = None
) -> dict[str, pd.DataFrame]:
    """Regime-switching random walk with volume that rises on large moves.

    Each ticker gets a different random length so that short-history cases
    (like a recent IPO) are exercised too.
    """
    rng = np.random.default_rng(seed)
    end_ts = pd.Timestamp(end) if end else pd.Timestamp.today().normalize()
    out: dict[str, pd.DataFrame] = {}
    for i, t in enumerate(tickers):
        n = n_days if i % 4 else max(120, n_days // 8)  # every 4th is "young"
        idx = pd.bdate_range(end=end_ts, periods=n)
        regime = np.cumsum(rng.normal(0, 0.02, n))  # slow-moving drift
        drift = 0.0006 * np.tanh(regime * 5)
        vol = 0.02 + 0.01 * rng.random()
        rets = drift + rng.normal(0, vol, n)
        close = 100 * np.exp(np.cumsum(rets))
        open_ = close * np.exp(rng.normal(0, vol / 3, n))
        high = np.maximum(open_, close) * np.exp(np.abs(rng.normal(0, vol / 2, n)))
        low = np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0, vol / 2, n)))
        base = rng.uniform(2e6, 2e7)
        volume = base * np.exp(rng.normal(0, 0.3, n)) * (1 + 15 * np.abs(rets))
        out[t] = pd.DataFrame(
            {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
            index=idx,
        )
    return out


def load(
    tickers: list[str],
    source: str = "yahoo",
    period: str = "5y",
    cache_dir: Path | None = None,
) -> dict[str, pd.DataFrame]:
    if source == "synthetic":
        return load_synthetic(tickers)
    if source != "yahoo":
        raise ValueError(f"unknown data source: {source}")

    data = load_yahoo(tickers, period=period)
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        for t, frame in data.items():
            frame.to_csv(cache_dir / f"{t}.csv")
    return data


def load_cache(tickers: list[str], cache_dir: Path) -> dict[str, pd.DataFrame]:
    """Read previously cached CSVs (lets the evaluation run without re-downloading)."""
    out = {}
    for t in tickers:
        path = cache_dir / f"{t}.csv"
        if path.exists():
            out[t] = _normalise(pd.read_csv(path, index_col=0, parse_dates=True))
    return out
