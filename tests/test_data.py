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


def test_yahoo_loader_retries_symbols_dropped_from_a_batch(monkeypatch):
    import sys
    import types

    from monitor import data as data_mod

    idx = pd.bdate_range("2026-01-02", periods=5)
    bars = pd.DataFrame({"Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0, "Volume": 1.0}, index=idx)
    calls = []

    def fake_download(tickers, **kwargs):
        calls.append(list(tickers))
        ok = [t for t in tickers if not (t == "AMZN" and len(calls) == 1)]  # AMZN fails the first time
        frames = {t: bars for t in ok}
        if len(tickers) == 1:
            return frames.get(tickers[0], pd.DataFrame())
        return pd.concat(frames, axis=1) if frames else pd.DataFrame()

    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(download=fake_download))
    out = data_mod.load_yahoo(["NVDA", "AMZN"], period="1mo")
    assert sorted(out) == ["AMZN", "NVDA"]
    assert calls == [["NVDA", "AMZN"], ["AMZN"]]
