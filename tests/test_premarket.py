from datetime import time

import numpy as np
import pandas as pd
import pytest

from monitor.data import trim_to_listing
from monitor.intraday import NY, _normalise, daily_from_intraday, load_synthetic_intraday
from monitor.premarket import premarket_features, score_premarket, session_table
from monitor.premarket_eval import evaluate_premarket

ASOF = pd.Timestamp("2026-11-04 08:40", tz=NY)
TICKERS = ["NVDA", "TSLA", "SKHY"]


@pytest.fixture(scope="module")
def live():
    intr = load_synthetic_intraday([*TICKERS, "SPY"], n_days=30, interval_minutes=5, asof=ASOF, seed=5)
    daily = {t: d[d.index < pd.Timestamp("2026-11-04")] for t, d in daily_from_intraday(intr).items()}
    return intr, daily


def _bars(day: str, times: list[str], closes: list[float], vols: list[float]) -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp(f"{day} {t}") for t in times]).tz_localize(NY)
    c = np.array(closes, dtype=float)
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": vols}, index=idx)


def test_session_table_boundaries():
    d1 = _bars("2026-11-02", ["08:00", "09:25", "09:30", "15:55", "16:00", "19:55"],
               [10, 11, 12, 13, 50, 60], [5, 5, 100, 100, 7, 7])
    d2 = _bars("2026-11-03", ["04:00", "08:30", "08:55", "09:30", "15:55"],
               [14, 15, 16, 17, 18], [1, 2, 3, 100, 100])
    s = session_table(pd.concat([d1, d2]), cutoff=time(9, 0), interval=pd.Timedelta(minutes=5))
    day2 = s.loc[pd.Timestamp("2026-11-03")]
    assert day2["pm_last"] == 16          # 08:55 bar closes at 09:00, exactly at the cutoff
    assert day2["prev_close"] == 13       # regular close, not the 16:00+ post-market prints
    assert day2["reg_open"] == 17 and day2["reg_close"] == 18
    assert day2["gap"] == pytest.approx(16 / 13 - 1)


def test_bar_must_close_before_cutoff():
    d = _bars("2026-11-03", ["08:30", "08:55"], [10, 20], [1, 1])
    s = session_table(d, cutoff=time(8, 58), interval=pd.Timedelta(minutes=5))
    assert s["pm_last"].iloc[0] == 10     # 08:55 bar closes 09:00, after the cutoff


def test_future_bars_do_not_change_snapshot(live):
    intr, daily = live
    cutoff = time(8, 0)
    a = premarket_features(intr, daily, TICKERS, "SPY", cutoff=cutoff)
    shocked = {}
    for t, f in intr.items():
        f = f.copy()
        start = f.index.hour * 60 + f.index.minute
        late = start + 5 > 8 * 60  # every bar that closes after 08:00, on every day
        f.loc[late, ["Open", "High", "Low", "Close"]] *= 1.5
        f.loc[late, "Volume"] *= 10
        shocked[t] = f
    # Context comes from completed sessions, which the shock also changes, so
    # compare only the pre-market inputs for the snapshot day.
    b = premarket_features(shocked, daily, TICKERS, "SPY", cutoff=cutoff)
    today = pd.Timestamp("2026-11-04")
    cols = ["pm_last", "pm_volume"]
    pd.testing.assert_frame_equal(a.xs(today, level="date")[cols], b.xs(today, level="date")[cols])


def test_context_uses_previous_session_only(live):
    intr, daily = live
    full = {t: daily_from_intraday({t: intr[t]})[t] for t in intr}  # includes no 11-04 regular bars
    a = premarket_features(intr, daily, TICKERS, "SPY")
    tampered = {t: d.copy() for t, d in full.items()}
    for d in tampered.values():
        d.loc[d.index[-1], ["High", "Close"]] *= 2  # last completed session
    b = premarket_features(intr, tampered, TICKERS, "SPY")
    prev_day = daily["NVDA"].index[-1]
    # The tampered session only affects dates *after* it.
    pd.testing.assert_series_equal(a.xs(prev_day, level="date")["ctx_score"],
                                   b.xs(prev_day, level="date")["ctx_score"])


def test_rvol_baseline_is_same_clock_time_and_past_only():
    days = pd.bdate_range("2026-10-01", periods=12)
    frames = [_bars(str(d.date()), ["07:00", "09:00"], [10, 10], [100, 900]) for d in days]
    s = session_table(pd.concat(frames), cutoff=time(8, 0), interval=pd.Timedelta(minutes=5))
    # Only the 07:00 bar is before 08:00, every day has 100 -> RVOL exactly 1.
    assert s["pm_rvol"].dropna().eq(1.0).all()
    assert s["pm_rvol"].iloc[:5].isna().all()  # needs >= 5 earlier sessions


def test_zero_extended_hours_volume_is_missing_not_quiet():
    days = pd.bdate_range("2026-10-01", periods=8)
    frames = [_bars(str(d.date()), ["07:00", "09:30"], [10, 10], [0, 500]) for d in days]
    s = session_table(pd.concat(frames), cutoff=time(9, 0), interval=pd.Timedelta(minutes=5))
    assert s["pm_rvol"].isna().all()


def test_scores_bounded_and_gap_down_volume_discount(live):
    intr, daily = live
    f = premarket_features(intr, daily, TICKERS, "SPY", cutoff=time(8, 40))
    s = score_premarket(f)
    assert s["pm_score"].dropna().between(0, 100).all()
    row = f.iloc[[0]].copy()
    row[["gap", "gap_atr", "pm_rvol"]] = [0.03, 1.0, 3.0]
    up = score_premarket(row)["pm_pts_volume"].iloc[0]
    row[["gap", "gap_atr"]] = [-0.03, -1.0]
    down = score_premarket(row)["pm_pts_volume"].iloc[0]
    assert down == pytest.approx(up * 0.25)


def test_no_premarket_price_is_insufficient():
    df = pd.DataFrame({"pm_last": [np.nan], "gap": [np.nan], "gap_atr": [np.nan], "pm_rvol": [np.nan],
                       "vs_high20": [np.nan], "ctx_score": [80.0]})
    out = score_premarket(df).iloc[0]
    assert out["pm_label"] == "INSUFFICIENT DATA" and np.isnan(out["pm_score"])


def test_utc_input_converts_to_new_york_across_dst():
    # 13:00 UTC is 09:00 EDT before 1 Nov 2026 and 08:00 EST after it.
    idx = pd.DatetimeIndex(["2026-10-30 13:00", "2026-11-02 13:00"], tz="UTC")
    f = pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0, "Volume": 1.0}, index=idx)
    local = _normalise(f).index
    assert [t.hour for t in local] == [9, 8]


def test_listing_trim_works_on_intraday_index():
    idx = pd.date_range("2026-06-10 04:00", periods=200, freq="1h", tz=NY)
    f = pd.DataFrame({"Close": 1.0}, index=idx)
    out = trim_to_listing({"SPCX": f}, {"SPCX": "2026-06-12"})
    assert out["SPCX"].index.min() == pd.Timestamp("2026-06-12 00:00", tz=NY)


def test_evaluate_premarket_end_to_end():
    intr = load_synthetic_intraday([*TICKERS, "SPY"], n_days=160, interval_minutes=60, seed=9)
    res = evaluate_premarket(intr, daily_from_intraday(intr), TICKERS, "SPY", reps=100)
    assert res.n_obs > 200
    assert -1 <= res.ic[0] <= 1
    assert set(res.ablation.index) == {"gap", "volume", "level", "context"}
    assert "Gap vs SPY only" in res.baselines.index
