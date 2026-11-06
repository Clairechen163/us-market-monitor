from datetime import time

import numpy as np
import pandas as pd
import pytest

from monitor import alpaca, live
from monitor.intraday import NY, daily_from_intraday, load_synthetic_intraday

T, B = ["NVDA", "TSLA", "IBM"], "SPY"


def ny(s):
    return pd.Timestamp(s, tz=NY)


def setup(now: str, seed: int = 8, days: int = 60):
    now = ny(now)
    data_end = now - pd.Timedelta(minutes=16)
    intr = load_synthetic_intraday([*T, B], n_days=days, interval_minutes=5, asof=data_end, seed=seed)
    return now, data_end, intr, daily_from_intraday(intr)


@pytest.mark.parametrize("when,phase", [
    ("2026-11-06 03:59", "closed"), ("2026-11-06 04:00", "premarket"), ("2026-11-06 09:29", "premarket"),
    ("2026-11-06 09:30", "regular"), ("2026-11-06 15:59", "regular"), ("2026-11-06 16:00", "after"),
    ("2026-11-06 20:00", "closed"), ("2026-11-07 10:00", "closed"),  # Saturday
    ("2026-07-06 09:45", "regular"),  # summer time (EDT)
])
def test_market_phase(when, phase):
    assert live.market_phase(ny(when)) == phase


def test_live_price_prefers_newer_iex_trade_from_today():
    now, data_end, intr, _ = setup("2026-11-06 11:20")
    last_bar_close = intr["NVDA"]["Close"].iloc[-1]
    trades = {"NVDA": {"price": 123.0, "time": now - pd.Timedelta(seconds=3)},
              "TSLA": {"price": 999.0, "time": ny("2026-11-05 15:59")}}  # yesterday's trade: ignore
    p = live.live_prices(intr, trades, now.tz_localize(None).normalize())
    assert p.loc["NVDA", "price"] == 123.0 and p.loc["NVDA", "price_source"] == "IEX real-time"
    assert p.loc["TSLA", "price"] == intr["TSLA"]["Close"].iloc[-1]
    assert p.loc["TSLA", "price_source"].startswith("all exchanges")
    assert last_bar_close != 123.0


def test_time_of_day_rvol_compares_the_same_window():
    days = pd.bdate_range("2026-10-01", periods=25)
    frames = []
    for i, d in enumerate(days):
        idx = pd.DatetimeIndex([pd.Timestamp(f"{d.date()} 09:30"), pd.Timestamp(f"{d.date()} 13:00")]).tz_localize(NY)
        vol = [200.0 if i == len(days) - 1 else 100.0, 10_000.0]  # the 13:00 bar is outside an 11:00 cutoff
        frames.append(pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0, "Volume": vol}, index=idx))
    rv = live.time_of_day_rvol(pd.concat(frames), time(11, 0))
    assert rv.iloc[-1] == pytest.approx(2.0)
    assert rv.iloc[-2] == pytest.approx(1.0)


def test_live_premarket_uses_live_price_and_delayed_volume():
    now, data_end, intr, daily = setup("2026-11-06 08:10")
    trades = {s: {"price": float(f["Close"].iloc[-1]) * 1.01, "time": now - pd.Timedelta(seconds=5)}
              for s, f in intr.items()}
    df, cutoff = live.live_premarket(intr, daily, trades, T, B, now, data_end)
    assert cutoff == time(7, 50)  # 08:10 minus the 15-minute delay, on a 5-minute boundary
    assert set(df.index) == set(T)
    for s in T:
        assert df.loc[s, "pm_last"] == pytest.approx(trades[s]["price"])
        assert df.loc[s, "gap"] == pytest.approx(trades[s]["price"] / df.loc[s, "prev_close"] - 1)
    assert df["pm_rvol"].notna().all() and df["pm_score"].between(0, 100).all()


def test_live_intraday_scores_today_with_the_live_close():
    now, data_end, intr, daily = setup("2026-11-06 11:20")
    trades = {s: {"price": float(f["Close"].iloc[-1]) * 0.99, "time": now - pd.Timedelta(seconds=5)}
              for s, f in intr.items()}
    df, cutoff = live.live_intraday(intr, daily, trades, T, B, now, data_end)
    assert cutoff == time(11, 0)
    for s in T:
        assert df.loc[s, "Close"] == pytest.approx(trades[s]["price"])
        assert df.loc[s, "prev_close"] == daily[s]["Close"][daily[s].index < pd.Timestamp("2026-11-06")].iloc[-1]
    assert df["score"].between(0, 100).all() and df["rvol20"].notna().all()


def test_latest_close_includes_today_only_after_the_session():
    for when, expected in [("2026-11-06 12:00", "2026-11-05"), ("2026-11-06 17:00", "2026-11-06")]:
        now, data_end, intr, daily = setup(when)
        snap = live.latest_close(daily, T, B, now, data_end)
        assert set(pd.to_datetime(snap["date"]).dt.strftime("%Y-%m-%d")) == {expected}


def test_holiday_gives_empty_live_tables():
    # Data ends the previous session: nothing traded "today".
    now, data_end, intr, daily = setup("2026-11-06 10:30")
    stale = {s: f[f.index < ny("2026-11-06 00:00")] for s, f in intr.items()}
    assert live.live_intraday(stale, daily, {}, T, B, now, data_end)[0].empty
    assert live.live_premarket(stale, daily, {}, T, B, ny("2026-11-06 08:00"), data_end)[0].empty


# ------------------------------------------------------------------- Alpaca live calls
class FakeResponse:
    def __init__(self, payload):
        self.status_code, self._payload, self.headers, self.text = 200, payload, {}, str(payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads, self.urls = list(payloads), []

    def get(self, url, params, headers, timeout):
        self.urls.append((url, dict(params)))
        return FakeResponse(self.payloads.pop(0))


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv(alpaca.KEY_ENV, "key")
    monkeypatch.setenv(alpaca.SECRET_ENV, "secret")


@pytest.mark.parametrize("wrap", [False, True])
def test_latest_trades_parse_snapshots(creds, wrap):
    body = {"NVDA": {"latestTrade": {"t": "2026-11-06T15:42:13.123456789Z", "p": 201.5, "s": 100}},
            "TSLA": {"latestTrade": None}}
    session = FakeSession([{"snapshots": body} if wrap else body])
    out = alpaca.load_latest_trades(["NVDA", "TSLA"], session=session)
    assert list(out) == ["NVDA"] and out["NVDA"]["price"] == 201.5
    assert out["NVDA"]["time"].strftime("%H:%M:%S") == "10:42:13"  # 15:42 UTC = 10:42 EST
    url, params = session.urls[0]
    assert url == alpaca.SNAPSHOTS_URL and params == {"symbols": "NVDA,TSLA", "feed": "iex"}


def test_daily_bars_are_indexed_by_new_york_date(creds):
    session = FakeSession([{"bars": {"NVDA": [
        {"t": "2026-11-05T05:00:00Z", "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 1e6},
        {"t": "2026-11-06T05:00:00Z", "o": 1.5, "h": 2, "l": 1, "c": 1.8, "v": 2e6}]}}])
    data, feed = alpaca.load_alpaca_daily(["NVDA"], ny("2026-11-01"), ny("2026-11-06 12:00"), session=session)
    idx = data["NVDA"].index
    assert idx.tz is None and [d.strftime("%Y-%m-%d") for d in idx] == ["2026-11-05", "2026-11-06"]
    assert session.urls[0][1]["timeframe"] == "1Day" and feed == "sip"
    assert np.isclose(data["NVDA"]["Close"].iloc[-1], 1.8)
