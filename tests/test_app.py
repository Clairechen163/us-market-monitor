"""Smoke-test the Streamlit dashboard in every market phase, with mocked data."""

from pathlib import Path

import pandas as pd
import pytest

st = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from monitor import alpaca  # noqa: E402
from monitor.intraday import NY, daily_from_intraday, load_synthetic_intraday  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


@pytest.fixture
def mocked(monkeypatch):
    monkeypatch.setenv(alpaca.KEY_ENV, "key")
    monkeypatch.setenv(alpaca.SECRET_ENV, "secret")

    def intraday(symbols, start, end, timeframe):
        return load_synthetic_intraday(symbols, n_days=45, interval_minutes=5, asof=end, seed=6), "sip"

    def daily(symbols, start, end):
        return daily_from_intraday(load_synthetic_intraday(symbols, n_days=45, interval_minutes=5, asof=end, seed=6)), "sip"

    def trades(symbols, feed="iex"):
        now = pd.Timestamp(__import__("os").environ["MONITOR_ASOF"], tz=NY)
        return {s: {"price": 100.0, "time": now - pd.Timedelta(seconds=2)} for s in symbols}

    monkeypatch.setattr(alpaca, "load_alpaca_intraday", intraday)
    monkeypatch.setattr(alpaca, "load_alpaca_daily", daily)
    monkeypatch.setattr(alpaca, "load_latest_trades", trades)
    st.cache_data.clear()


@pytest.mark.parametrize("asof,heading", [
    ("2026-11-06 08:20", "Pre-market · live"),
    ("2026-11-06 11:30", "Regular session · live"),
    ("2026-11-06 17:30", "After the close"),
    ("2026-11-07 12:00", "Market closed"),
])
def test_dashboard_renders_each_phase(mocked, monkeypatch, asof, heading):
    monkeypatch.setenv("MONITOR_ASOF", asof)
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, at.exception
    assert any(h.value.startswith(heading) for h in at.subheader)
    assert len(at.dataframe) == 1


def test_dashboard_explains_missing_keys(monkeypatch):
    monkeypatch.delenv(alpaca.KEY_ENV, raising=False)
    monkeypatch.delenv(alpaca.SECRET_ENV, raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert any("ALPACA_API_KEY_ID" in e.value for e in at.error)
