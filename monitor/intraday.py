"""Intraday bars including extended hours (pre-market 04:00-09:30 ET).

All intraday frames use a tz-aware America/New_York index, so session
boundaries are correct through daylight-saving changes.

Sources:
* ``yahoo``     - yfinance with ``prepost=True``. Yahoo limits history by
                  interval: 5-minute bars for ~60 days, hourly bars for ~730 days.
* ``synthetic`` - simulated 04:00-20:00 sessions for tests and offline demos.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import LISTING_DATES
from .data import OHLCV, trim_to_listing

NY = "America/New_York"


def _normalise(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame[OHLCV].copy()
    idx = pd.to_datetime(frame.index, utc=True).tz_convert(NY).as_unit("ns")
    frame.index = idx
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    frame = frame.dropna(subset=["Close"])
    frame["Volume"] = frame["Volume"].fillna(0.0)
    return frame.astype(float)


def load_yahoo_intraday(tickers: list[str], period: str, interval: str,
                        retry: bool = True) -> dict[str, pd.DataFrame]:
    """Raw (unadjusted) intraday bars with pre- and post-market sessions.

    Failed symbols are requested once more on their own (see data.load_yahoo).
    """
    import yfinance as yf

    raw = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        prepost=True,
        auto_adjust=False,
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
    missing = [t for t in tickers if t not in out]
    if missing and retry:
        out.update(load_yahoo_intraday(missing, period=period, interval=interval, retry=False))
    return trim_to_listing(out, LISTING_DATES)


def save_cache(data: dict[str, pd.DataFrame], cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    for t, frame in data.items():
        frame.to_csv(cache_dir / f"{t}.csv")


def load_cache(tickers: list[str], cache_dir: Path) -> dict[str, pd.DataFrame]:
    out = {}
    for t in tickers:
        path = cache_dir / f"{t}.csv"
        if path.exists():
            out[t] = _normalise(pd.read_csv(path, index_col=0))
    return trim_to_listing(out, LISTING_DATES)


def load_synthetic_intraday(
    tickers: list[str],
    n_days: int = 60,
    interval_minutes: int = 5,
    seed: int = 3,
    end: str | pd.Timestamp | None = None,
    asof: pd.Timestamp | None = None,
) -> dict[str, pd.DataFrame]:
    """Simulated 04:00-20:00 ET sessions on business days.

    Pre- and post-market bars are thin (low volume) and include an overnight
    news shock, so gaps happen. If ``asof`` is given, bars after it are
    removed, which mimics a live run during the pre-market.
    """
    rng = np.random.default_rng(seed)
    end_day = pd.Timestamp(end or (asof.tz_convert(NY).tz_localize(None) if asof is not None
                                   else pd.Timestamp.today())).normalize()
    days = pd.bdate_range(end=end_day, periods=n_days)
    step = pd.Timedelta(minutes=interval_minutes)
    per_day = int(16 * 60 / interval_minutes)  # 04:00 -> 20:00
    offsets = np.arange(per_day) * step + pd.Timedelta(hours=4)
    tod_min = (offsets / pd.Timedelta(minutes=1)).astype(int)
    is_reg = (tod_min >= 570) & (tod_min < 960)

    out = {}
    for t in tickers:
        sigma_day = 0.015 + 0.015 * rng.random()
        sigma_bar = sigma_day / np.sqrt(per_day)
        base_vol = rng.uniform(5e4, 5e5) * interval_minutes
        price = 100.0
        frames = []
        for d in days:
            ts = pd.DatetimeIndex(d + offsets).tz_localize(NY)
            rets = rng.normal(0, sigma_bar, per_day)
            rets[0] += rng.normal(0, sigma_day * 0.6)  # overnight news at 04:00
            close = price * np.exp(np.cumsum(rets))
            open_ = np.concatenate([[price], close[:-1]])
            wiggle = np.abs(rng.normal(0, sigma_bar, (2, per_day)))
            high = np.maximum(open_, close) * np.exp(wiggle[0])
            low = np.minimum(open_, close) * np.exp(-wiggle[1])
            shock = 1 + 40 * abs(rets[0])  # big overnight news -> busy pre-market
            vol = base_vol * np.exp(rng.normal(0, 0.4, per_day)) * np.where(is_reg, 1.0, 0.05 * shock)
            frames.append(pd.DataFrame(
                {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol}, index=ts))
            price = close[-1]
        frame = pd.concat(frames)
        if asof is not None:
            frame = frame[frame.index + step <= asof]
        out[t] = frame
    return out


def daily_from_intraday(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Regular-session daily OHLCV built from intraday bars (synthetic mode)."""
    out = {}
    for t, f in data.items():
        tod = f.index.hour * 60 + f.index.minute
        reg = f[(tod >= 570) & (tod < 960)]
        day = reg.index.tz_localize(None).normalize()
        g = reg.groupby(day)
        daily = pd.DataFrame({"Open": g["Open"].first(), "High": g["High"].max(),
                              "Low": g["Low"].min(), "Close": g["Close"].last(),
                              "Volume": g["Volume"].sum()})
        out[t] = daily
    return out
