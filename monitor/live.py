"""Live scores for the web dashboard, using the same rules as the daily monitors.

Data available on Alpaca's free plan:
* prices: real-time latest trades from the IEX exchange;
* volume and bars: every U.S. exchange (SIP), except the most recent 15 minutes.

So each live score combines a real-time price with full-market volume up to
~15 minutes ago. Volume is always compared with the *same clock time* on
earlier days, which keeps the comparison fair even though today's figure is
slightly delayed.

Phases (New York time, weekdays):
    premarket  04:00-09:30   live pre-market score
    regular    09:30-16:00   live intraday version of the end-of-day score
    after      16:00-20:00   end-of-day score for today's close
    closed     otherwise     end-of-day score for the latest close
"""

from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd

from .indicators import add_indicators
from .intraday import NY
from .pipeline import build_panel, latest_snapshot
from .premarket import REG_CLOSE, REG_OPEN, PRE_OPEN, premarket_features, score_premarket, session_table
from .scoring import score_frame

POST_CLOSE = time(20, 0)


def market_phase(now: pd.Timestamp) -> str:
    now = now.tz_convert(NY)
    if now.weekday() >= 5:
        return "closed"
    t = now.time()
    if PRE_OPEN <= t < REG_OPEN:
        return "premarket"
    if REG_OPEN <= t < REG_CLOSE:
        return "regular"
    if REG_CLOSE <= t < POST_CLOSE:
        return "after"
    return "closed"


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def live_prices(intraday: dict[str, pd.DataFrame], trades: dict[str, dict],
                today: pd.Timestamp, step: pd.Timedelta = pd.Timedelta(minutes=5)) -> pd.DataFrame:
    """Most recent price per symbol: the IEX real-time trade if it is from today
    and newer than the last full-market bar, otherwise that bar's close."""
    rows = {}
    for sym in set(intraday) | set(trades):
        best = None
        bars = intraday.get(sym)
        if bars is not None and len(bars):
            last = bars[bars.index.tz_localize(None).normalize() == today]
            if len(last):
                best = (float(last["Close"].iloc[-1]), last.index[-1] + step, "all exchanges (15-min delayed)")
        tr = trades.get(sym)
        if tr is not None and tr["time"].tz_convert(NY).tz_localize(None).normalize() == today:
            if best is None or tr["time"] > best[1]:
                best = (tr["price"], tr["time"].tz_convert(NY), "IEX real-time")
        if best is not None:
            rows[sym] = {"price": best[0], "price_time": best[1], "price_source": best[2]}
    return pd.DataFrame.from_dict(rows, orient="index")


def time_of_day_rvol(bars: pd.DataFrame, cutoff: time, window: int = 20,
                     bar: pd.Timedelta = pd.Timedelta(minutes=5)) -> pd.Series:
    """Regular-session volume from 09:30 up to ``cutoff``, divided by the
    average over the same clock window on the previous ``window`` sessions.
    ``bar`` is the bar length; a bar counts only if it closed by the cutoff."""
    step = int(bar / pd.Timedelta(minutes=1))
    start = bars.index.hour * 60 + bars.index.minute
    day = bars.index.tz_localize(None).normalize().as_unit("ns")
    reg = (start >= _minutes(REG_OPEN)) & (start + step <= _minutes(cutoff))
    vol = bars["Volume"][reg].groupby(day[reg]).sum()
    vol = vol.where(vol > 0)
    baseline = vol.shift(1).rolling(window, min_periods=max(3, window // 2)).mean()
    return vol / baseline


def _data_cutoff(data_end: pd.Timestamp, cap: time) -> time:
    t = data_end.tz_convert(NY).floor("5min").time()
    return min(t, cap)


def live_premarket(intraday, daily, trades, tickers, benchmark, now, data_end) -> tuple[pd.DataFrame, time]:
    """Live pre-market score: real-time price, volume through the delayed cutoff."""
    today = now.tz_convert(NY).tz_localize(None).normalize()
    cutoff = max(PRE_OPEN, _data_cutoff(data_end, REG_OPEN))
    feats = premarket_features(intraday, daily, tickers, benchmark, cutoff=cutoff)
    if today not in feats.index.get_level_values("date"):
        return pd.DataFrame(), cutoff
    snap = feats.xs(today, level="date").copy()
    prices = live_prices(intraday, trades, today)

    def gap_for(sym, prev_close):
        if sym in prices.index and np.isfinite(prev_close):
            return prices.loc[sym, "price"] / prev_close - 1.0
        return np.nan

    bench_gap = np.nan
    if benchmark in intraday:
        b = session_table(intraday[benchmark], cutoff)
        if today in b.index:
            bench_gap = gap_for(benchmark, b.loc[today, "prev_close"])
    for sym in snap.index:
        if sym in prices.index:
            snap.loc[sym, "pm_last"] = prices.loc[sym, "price"]
    snap["gap"] = [gap_for(s, pc) for s, pc in zip(snap.index, snap["prev_close"])]
    snap["excess_gap"] = snap["gap"] - bench_gap
    gap_x = snap["excess_gap"].where(snap["excess_gap"].notna(), snap["gap"])
    snap["gap_atr"] = gap_x / snap["atr14_pct"]
    snap["vs_high20"] = snap["pm_last"] / snap["high20"] - 1.0
    snap = snap[snap["pm_last"].notna()]
    out = snap.join(score_premarket(snap)).join(prices, how="left")
    return out.sort_values("pm_score", ascending=False, na_position="last"), cutoff


def _provisional_bar(bars: pd.DataFrame | None, today: pd.Timestamp, price: float) -> pd.DataFrame:
    """Today's daily bar so far: regular-session bars plus the live price."""
    o = h = lo = price
    v = np.nan
    if bars is not None and len(bars):
        start = bars.index.hour * 60 + bars.index.minute
        day = bars.index.tz_localize(None).normalize()
        reg = bars[(day == today) & (start >= _minutes(REG_OPEN)) & (start < _minutes(REG_CLOSE))]
        if len(reg):
            o, h, lo, v = reg["Open"].iloc[0], max(reg["High"].max(), price), min(reg["Low"].min(), price), reg["Volume"].sum()
    return pd.DataFrame({"Open": [o], "High": [h], "Low": [lo], "Close": [price], "Volume": [v]},
                        index=pd.DatetimeIndex([today]).as_unit("ns"))


def live_intraday(intraday, daily, trades, tickers, benchmark, now, data_end) -> tuple[pd.DataFrame, time]:
    """Live version of the end-of-day score during the regular session.

    Today's provisional bar uses the live price as its close. RVOL compares
    volume since 09:30 with the same window on the previous 20 sessions
    (a full-day RVOL would always look low mid-session).
    """
    today = now.tz_convert(NY).tz_localize(None).normalize()
    cutoff = _data_cutoff(data_end, REG_CLOSE)
    prices = live_prices(intraday, trades, today)
    completed = {t: d[d.index < today] for t, d in daily.items()}

    def with_today(sym):
        if sym not in completed or sym not in prices.index:
            return None
        bar = _provisional_bar(intraday.get(sym), today, prices.loc[sym, "price"])
        return pd.concat([completed[sym], bar])

    bench = with_today(benchmark) if benchmark else None
    rows = []
    for sym in tickers:
        frame = with_today(sym)
        if frame is None:
            continue
        ind = add_indicators(frame, bench["Close"] if bench is not None else None)
        rv = time_of_day_rvol(intraday[sym], cutoff) if sym in intraday else pd.Series(dtype=float)
        ind.loc[today, "rvol20"] = rv.get(today, np.nan)
        row = ind.loc[[today]].join(score_frame(ind.loc[[today]]))
        row.index = [sym]
        rows.append(row)
    if not rows:
        return pd.DataFrame(), cutoff
    out = pd.concat(rows).join(prices, how="left")
    out["prev_close"] = [completed[s]["Close"].iloc[-1] for s in out.index]
    return out.sort_values("score", ascending=False, na_position="last"), cutoff


def latest_close(daily, tickers, benchmark, now, data_end) -> pd.DataFrame:
    """End-of-day scores at the latest completed close."""
    today = now.tz_convert(NY).tz_localize(None).normalize()
    session_done = data_end.tz_convert(NY).time() >= REG_CLOSE and data_end.tz_convert(NY).tz_localize(None).normalize() == today
    usable = {t: (d if session_done else d[d.index < today]) for t, d in daily.items()}
    snap = latest_snapshot(build_panel(usable, [t for t in tickers if t in usable], benchmark))
    snap["price"] = snap["Close"]
    return snap.sort_values("score", ascending=False, na_position="last")
