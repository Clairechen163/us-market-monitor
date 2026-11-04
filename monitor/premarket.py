"""Pre-market features and score.

Session boundaries (America/New_York):
    pre-market  04:00 - 09:30
    regular     09:30 - 16:00
    post-market 16:00 - 20:00

A pre-market snapshot "as of" clock time C uses only bars that have fully
closed by C on that day (bar start + bar length <= C, with C <= 09:30).
Every historical day is evaluated at the same clock time C, so today's
pre-market volume is always compared with volume over the *same* part of
the morning on earlier days.

Features per (date, ticker)
---------------------------
gap          last pre-market price / previous regular-session close - 1
excess_gap   gap minus SPY's gap over the same window
gap_atr      excess_gap divided by the stock's ATR14 (as % of price), so a 3%
             gap means more for ETN than for TSLA
pm_rvol      pre-market volume / mean pre-market volume of the previous
             PREMARKET_RVOL_WINDOW sessions up to the same clock time
vs_high20    last pre-market price vs the highest high of the prior 20 sessions
ctx_score    end-of-day score at the previous close (no look-ahead)
"""

from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from .config import (
    BENCHMARK, INSUFFICIENT_LABEL, MIN_COVERAGE, PREMARKET_RVOL_WINDOW, PREMARKET_WEIGHTS,
)
from .pipeline import build_panel
from .scoring import _interp, _weighted_parts, label_for

PRE_OPEN = time(4, 0)
REG_OPEN = time(9, 30)
REG_CLOSE = time(16, 0)
COMPONENTS = list(PREMARKET_WEIGHTS)


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def infer_interval(frame: pd.DataFrame) -> pd.Timedelta:
    diffs = pd.Series(frame.index).diff().dropna()
    diffs = diffs[diffs > pd.Timedelta(0)]
    return diffs.mode().iloc[0] if len(diffs) else pd.Timedelta(minutes=5)


def session_table(bars: pd.DataFrame, cutoff: time = REG_OPEN,
                  interval: pd.Timedelta | None = None) -> pd.DataFrame:
    """One row per New York trading date with pre-market and regular aggregates."""
    if _minutes(cutoff) > _minutes(REG_OPEN):
        raise ValueError("pre-market cutoff must be at or before 09:30 ET")
    interval = interval or infer_interval(bars)
    step = int(interval / pd.Timedelta(minutes=1))
    start = bars.index.hour * 60 + bars.index.minute
    day = bars.index.tz_localize(None).normalize()

    pre = (start >= _minutes(PRE_OPEN)) & (start + step <= _minutes(cutoff))
    reg = (start >= _minutes(REG_OPEN)) & (start < _minutes(REG_CLOSE))

    p = bars[pre].groupby(day[pre])
    pm = pd.DataFrame({
        "pm_last": p["Close"].last(),
        "pm_high": p["High"].max(),
        "pm_low": p["Low"].min(),
        "pm_volume": p["Volume"].sum(),
        "pm_bars": p.size(),
    })
    r = bars[reg].groupby(day[reg])
    rg = pd.DataFrame({"reg_open": r["Open"].first(), "reg_close": r["Close"].last()})

    out = pm.join(rg, how="outer").sort_index()
    out.index.name = "date"
    out["prev_close"] = out["reg_close"].ffill().shift(1)
    out["gap"] = out["pm_last"] / out["prev_close"] - 1.0
    # Same-clock-time baseline from earlier sessions only. Zero volume (Yahoo
    # sometimes omits extended-hours volume) counts as unknown, not as quiet.
    vol = out["pm_volume"].where(out["pm_volume"] > 0)
    baseline = vol.shift(1).rolling(PREMARKET_RVOL_WINDOW, min_periods=max(3, PREMARKET_RVOL_WINDOW // 2)).mean()
    out["pm_rvol"] = vol / baseline
    out["oc_ret"] = out["reg_close"] / out["reg_open"] - 1.0  # used only as an evaluation target
    return out


def daily_context(daily: dict[str, pd.DataFrame], tickers: list[str],
                  benchmark: str | None) -> pd.DataFrame:
    """End-of-day score, ATR% and 20-session high per (date, ticker)."""
    panel = build_panel(daily, tickers, benchmark)
    ctx = panel[["score", "coverage", "atr14_pct"]].copy()
    ctx["ctx_score"] = ctx["score"].where(ctx["coverage"] >= MIN_COVERAGE)
    highs = []
    for t in tickers:
        if t in daily:
            h = daily[t]["High"].rolling(20, min_periods=20).max()
            highs.append(pd.DataFrame({"date": h.index, "ticker": t, "high20": h.to_numpy()}))
    high20 = pd.concat(highs).set_index(["date", "ticker"])["high20"]
    ctx = ctx.join(high20)
    return ctx[["ctx_score", "atr14_pct", "high20"]]


def premarket_features(
    intraday: dict[str, pd.DataFrame],
    daily: dict[str, pd.DataFrame],
    tickers: list[str],
    benchmark: str | None = BENCHMARK,
    cutoff: time = REG_OPEN,
) -> pd.DataFrame:
    """Feature panel indexed by (date, ticker).

    Daily context is joined from the most recent session *strictly before*
    each date, so nothing from the regular session of that date leaks in.
    """
    interval = None
    bench = None
    if benchmark and benchmark in intraday:
        interval = infer_interval(intraday[benchmark])
        bench = session_table(intraday[benchmark], cutoff, interval)

    ctx = daily_context(daily, [t for t in tickers if t in daily], benchmark)
    frames = []
    for t in tickers:
        if t not in intraday:
            continue
        s = session_table(intraday[t], cutoff, interval or infer_interval(intraday[t]))
        if bench is not None:
            s["excess_gap"] = s["gap"] - bench["gap"].reindex(s.index)
            s["target"] = s["oc_ret"] - bench["oc_ret"].reindex(s.index)
        else:
            s["excess_gap"] = np.nan
            s["target"] = s["oc_ret"]
        s = s.reset_index()
        if t in ctx.index.get_level_values("ticker"):
            c = ctx.xs(t, level="ticker").reset_index().sort_values("date")
            s = pd.merge_asof(s.sort_values("date"), c, on="date",
                              direction="backward", allow_exact_matches=False)
        else:
            s[["ctx_score", "atr14_pct", "high20"]] = np.nan
        s["ticker"] = t
        frames.append(s)
    if not frames:
        raise RuntimeError("no intraday data for any ticker")
    out = pd.concat(frames).set_index(["date", "ticker"]).sort_index()
    gap_x = out["excess_gap"].where(out["excess_gap"].notna(), out["gap"])
    out["gap_atr"] = gap_x / out["atr14_pct"]
    out["vs_high20"] = out["pm_last"] / out["high20"] - 1.0
    return out


# ------------------------------------------------------------------- scoring
def _gap(df):
    return _weighted_parts([(_interp(df["gap_atr"], [-1.0, 0.0, 1.0], [0.0, 0.5, 1.0]),
                             PREMARKET_WEIGHTS["gap"])])


def _volume(df):
    frac = _interp(df["pm_rvol"], [0.5, 1.0, 2.0, 3.0], [0.0, 0.40, 0.75, 1.0])
    frac = frac.where(~(df["gap"] < 0), frac * 0.25)  # heavy selling is not support
    return _weighted_parts([(frac, PREMARKET_WEIGHTS["volume"])])


def _level(df):
    frac = _interp(df["vs_high20"], [-0.10, -0.05, 0.0, 0.03], [0.0, 0.30, 0.70, 1.0])
    return _weighted_parts([(frac, PREMARKET_WEIGHTS["level"])])


def _context(df):
    return _weighted_parts([((df["ctx_score"] / 100.0).clip(0, 1), PREMARKET_WEIGHTS["context"])])


_FUNCS = {"gap": _gap, "volume": _volume, "level": _level, "context": _context}


def score_premarket(df: pd.DataFrame, exclude: tuple[str, ...] = ()) -> pd.DataFrame:
    """0-100 pre-market score with the same coverage rules as the daily score."""
    out = pd.DataFrame(index=df.index)
    earned_total = pd.Series(0.0, index=df.index)
    available_total = pd.Series(0.0, index=df.index)
    possible = 0.0
    for name in COMPONENTS:
        if name in exclude:
            continue
        earned, available = _FUNCS[name](df)
        out[f"pm_pts_{name}"] = earned.where(available > 0)
        earned_total += earned
        available_total += available
        possible += PREMARKET_WEIGHTS[name]
    # Without a pre-market price there is nothing to score.
    no_price = df["pm_last"].isna()
    out["pm_coverage"] = (available_total / possible).where(~no_price, 0.0)
    out["pm_score"] = (100.0 * earned_total / available_total.replace(0, np.nan)).round(1).where(~no_price)
    out["pm_label"] = [label_for(s, c) for s, c in zip(out["pm_score"], out["pm_coverage"])]
    return out


def is_insufficient(label: str) -> bool:
    return label == INSUFFICIENT_LABEL
