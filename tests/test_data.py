import pandas as pd

from monitor.config import LISTING_DATES, TICKERS
from monitor.data import trim_to_listing


def test_listing_dates_cover_known_recent_listings():
    assert set(LISTING_DATES) <= set(TICKERS)
    assert {"SPCX", "SKHY"} <= set(LISTING_DATES)


def test_trim_drops_pre_listing_history_from_reused_symbol():
    idx = pd.bdate_range("2026-01-02", "2026-07-31")
    frame = pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0, "Volume": 1.0}, index=idx)
    out = trim_to_listing({"SPCX": frame, "NVDA": frame}, {"SPCX": "2026-06-12"})
    assert out["SPCX"].index.min() == pd.Timestamp("2026-06-12")
    assert len(out["NVDA"]) == len(frame)  # untouched
