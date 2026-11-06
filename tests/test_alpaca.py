from datetime import time

import pandas as pd
import pytest

import premarket_monitor
from monitor import alpaca
from monitor.intraday import NY


class FakeResponse:
    def __init__(self, status, payload=None, headers=None):
        self.status_code, self._payload, self.headers = status, payload or {}, headers or {}
        self.text = str(payload)

    def json(self):
        return self._payload


class FakeSession:
    """Replays queued responses and records the query parameters it was sent."""

    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, params, headers, timeout):
        self.calls.append(dict(params))
        assert headers["APCA-API-KEY-ID"] == "key" and headers["APCA-API-SECRET-KEY"] == "secret"
        return self.responses.pop(0)


def bar(t, c, v):
    return {"t": t, "o": c, "h": c, "l": c, "c": c, "v": v, "n": 1, "vw": c}


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv(alpaca.KEY_ENV, "key")
    monkeypatch.setenv(alpaca.SECRET_ENV, "secret")
    monkeypatch.setattr(alpaca._time, "sleep", lambda s: None)


START, END = pd.Timestamp("2026-11-04 00:00", tz=NY), pd.Timestamp("2026-11-05 08:39", tz=NY)


def test_pages_symbols_and_converts_utc_to_new_york(creds):
    session = FakeSession([
        FakeResponse(200, {"bars": {"NVDA": [bar("2026-11-05T09:00:00Z", 200.0, 1500)]},
                           "next_page_token": "abc"}),
        FakeResponse(200, {"bars": {"NVDA": [bar("2026-11-05T13:35:00Z", 201.0, 900)],
                                    "SPY": [bar("2026-11-05T09:00:00Z", 600.0, 5000)]},
                           "next_page_token": None}),
    ])
    data, feed = alpaca.load_alpaca_intraday(["NVDA", "SPY"], START, END, session=session)
    assert feed == "sip"
    nvda = data["NVDA"]
    # 09:00 UTC on 5 Nov 2026 is 04:00 EST, the start of the pre-market.
    assert [t.strftime("%H:%M") for t in nvda.index] == ["04:00", "08:35"]
    assert nvda["Volume"].tolist() == [1500.0, 900.0]
    assert list(nvda.columns) == ["Open", "High", "Low", "Close", "Volume"]
    first, second = session.calls
    assert first["feed"] == "sip" and first["adjustment"] == "split" and first["symbols"] == "NVDA,SPY"
    # 08:39 ET is rounded down to the last whole 5-minute bar (08:35 ET = 13:35 UTC).
    assert first["end"] == "2026-11-05T13:35:00Z" and "page_token" not in first
    assert second["page_token"] == "abc"


def test_retries_when_rate_limited(creds):
    session = FakeSession([
        FakeResponse(429, headers={"Retry-After": "1"}),
        FakeResponse(200, {"bars": {"NVDA": [bar("2026-11-05T09:00:00Z", 1.0, 1)]}}),
    ])
    data, _ = alpaca.load_alpaca_intraday(["NVDA"], START, END, session=session)
    assert len(data["NVDA"]) == 1 and len(session.calls) == 2


def test_falls_back_to_iex_when_sip_not_permitted(creds):
    refused = {"message": "subscription does not permit querying recent SIP data"}
    session = FakeSession([
        FakeResponse(403, refused),  # SIP up to the requested end
        FakeResponse(403, refused),  # SIP ending 16 minutes earlier
        FakeResponse(200, {"bars": {"NVDA": [bar("2026-11-05T09:00:00Z", 1.0, 10)]}}),
    ])
    data, feed = alpaca.load_alpaca_intraday(["NVDA"], START, END, session=session)
    assert feed == "iex" and [c["feed"] for c in session.calls] == ["sip", "sip", "iex"]


def test_bad_keys_raise_instead_of_silently_falling_back(creds):
    session = FakeSession([FakeResponse(401, {"message": "unauthorized."})])
    with pytest.raises(alpaca.AlpacaError, match="401"):
        alpaca.load_alpaca_intraday(["NVDA"], START, END, session=session)


def test_requires_credentials(monkeypatch):
    monkeypatch.delenv(alpaca.KEY_ENV, raising=False)
    monkeypatch.delenv(alpaca.SECRET_ENV, raising=False)
    assert not alpaca.have_credentials()
    with pytest.raises(alpaca.AlpacaError, match="ALPACA_API_KEY_ID"):
        alpaca.load_alpaca_intraday(["NVDA"], START, END, session=FakeSession([]))


def test_reused_symbol_history_is_trimmed(creds):
    # SPCX belonged to an ETF before SpaceX listed on 2026-06-12.
    session = FakeSession([FakeResponse(200, {"bars": {"SPCX": [
        bar("2026-04-01T13:30:00Z", 22.0, 100), bar("2026-06-12T13:30:00Z", 150.0, 9e6)]}})])
    data, _ = alpaca.load_alpaca_intraday(["SPCX"], START, END, session=session)
    assert data["SPCX"]["Close"].tolist() == [150.0]


@pytest.mark.parametrize("asof,data_end,expected", [
    ("2026-11-05 08:55", "2026-11-05 08:39", time(8, 30)),  # scheduled run: capped at the snapshot
    ("2026-11-05 06:10", "2026-11-05 05:54", time(5, 50)),  # early manual run: what the delay allows
    ("2026-11-05 04:10", "2026-11-05 03:54", time(4, 0)),   # nothing usable yet
    ("2026-11-05 15:00", "2026-11-05 14:44", time(8, 30)),  # after the open: still the 08:30 snapshot
])
def test_snapshot_cutoff_respects_delay_and_snapshot_time(asof, data_end, expected):
    got = premarket_monitor.snapshot_cutoff(pd.Timestamp(asof, tz=NY), pd.Timestamp(data_end, tz=NY), time(8, 30))
    assert got == expected


def test_auto_source_uses_alpaca_only_with_keys(monkeypatch):
    monkeypatch.delenv(alpaca.KEY_ENV, raising=False)
    monkeypatch.delenv(alpaca.SECRET_ENV, raising=False)
    assert premarket_monitor.resolve_source("auto") == "yahoo"
    monkeypatch.setenv(alpaca.KEY_ENV, "key")
    monkeypatch.setenv(alpaca.SECRET_ENV, "secret")
    assert premarket_monitor.resolve_source("auto") == "alpaca"


def _fake_sources(monkeypatch, alpaca_result):
    from monitor.intraday import daily_from_intraday, load_synthetic_intraday

    def fake_intraday(symbols, **kw):
        end = kw.get("end", pd.Timestamp("2026-11-04 08:55", tz=NY))
        return load_synthetic_intraday(symbols, n_days=30, interval_minutes=5, asof=end, seed=2)

    def fake_alpaca(symbols, start, end, timeframe):
        if isinstance(alpaca_result, Exception):
            raise alpaca_result
        return fake_intraday(symbols, end=end), alpaca_result

    def fake_daily(symbols, source, period):
        return daily_from_intraday(fake_intraday(symbols))

    monkeypatch.setattr(premarket_monitor.alpaca, "load_alpaca_intraday", fake_alpaca)
    monkeypatch.setattr(premarket_monitor, "load_daily", fake_daily)
    monkeypatch.setattr(premarket_monitor, "load_yahoo_intraday", lambda symbols, period, interval: fake_intraday(symbols))


@pytest.mark.parametrize("alpaca_result,expected_source", [
    ("sip", "alpaca-sip"),
    (alpaca.AlpacaError("HTTP 401: unauthorized."), "yahoo"),  # auto mode keeps working
])
def test_cli_uses_alpaca_and_labels_the_source(tmp_path, creds, monkeypatch, alpaca_result, expected_source):
    _fake_sources(monkeypatch, alpaca_result)
    out, docs = tmp_path / "pm", tmp_path / "docs"
    assert premarket_monitor.main(["--asof", "2026-11-04 08:55", "--outdir", str(out), "--docs", str(docs)]) == 0
    df = pd.read_csv(out / "premarket_20261104.csv", index_col="ticker")
    assert set(df["source"]) == {expected_source}
    assert set(df["bars_through"]) == {"08:30"}
    page = (docs / "premarket.md").read_text()
    assert premarket_monitor.DATA_NOTES[expected_source] in page


def test_premarket_evaluation_reads_alpaca_history(tmp_path, creds, monkeypatch):
    import importlib.util
    from pathlib import Path

    from monitor.intraday import daily_from_intraday, load_synthetic_intraday

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("evaluate_premarket", root / "scripts" / "evaluate_premarket.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    hist = load_synthetic_intraday(["NVDA", "TSLA", "AMZN", "SPY"], n_days=150, interval_minutes=30, seed=4)
    calls = []

    def fake_alpaca(symbols, start, end, timeframe):
        calls.append(timeframe)
        assert end == end.normalize(), "evaluation must stop at midnight ET (completed sessions only)"
        return {s: hist[s] for s in symbols}, "sip"

    monkeypatch.setattr(mod.alpaca, "load_alpaca_intraday", fake_alpaca)
    monkeypatch.setattr(mod, "load_daily", lambda symbols, source, period, cache_dir: daily_from_intraday(hist))
    args = ["--tickers", "NVDA", "TSLA", "AMZN", "--outdir", str(tmp_path / "docs"),
            "--cache", str(tmp_path / "cache"), "--reps", "50"]
    assert mod.main(args) == 0
    assert calls == ["30Min"]
    page = (tmp_path / "docs" / "premarket_evaluation.md").read_text()
    assert "Alpaca SIP feed" in page and "08:30 ET" in page
    # Second run reuses the cache instead of downloading again.
    assert mod.main(args) == 0 and calls == ["30Min"]


def test_scheduled_window_skips_a_late_early_trigger(tmp_path):
    # The 07:55 ET winter trigger starting late (08:01) must not publish a partial snapshot.
    out = tmp_path / "pm"
    assert premarket_monitor.main(["--source", "synthetic", "--asof", "2026-11-05 08:01",
                                   "--window", "08:46-09:45", "--outdir", str(out)]) == 0
    assert not out.exists()


def test_retries_temporary_server_errors(creds):
    session = FakeSession([FakeResponse(503), FakeResponse(502),
                           FakeResponse(200, {"bars": {"NVDA": [bar("2026-11-05T09:00:00Z", 1.0, 1)]}})])
    data, feed = alpaca.load_alpaca_intraday(["NVDA"], START, END, session=session)
    assert feed == "sip" and len(session.calls) == 3


def test_recent_sip_refusal_retries_earlier_before_using_iex(creds):
    session = FakeSession([
        FakeResponse(400, {"message": "end is too late for subscription"}),
        FakeResponse(200, {"bars": {"NVDA": [bar("2026-11-05T09:00:00Z", 1.0, 10)]}}),
    ])
    data, feed = alpaca.load_alpaca_intraday(["NVDA"], START, END, session=session)
    assert feed == "sip" and [c["feed"] for c in session.calls] == ["sip", "sip"]
    assert session.calls[1]["end"] < session.calls[0]["end"]


@pytest.mark.parametrize("timeframe,expected_end", [("5Min", "13:35"), ("30Min", "13:30"), ("1Hour", "13:00")])
def test_request_end_is_a_whole_bar(creds, timeframe, expected_end):
    session = FakeSession([FakeResponse(200, {"bars": {}})])
    alpaca.load_alpaca_intraday(["NVDA"], START, END, timeframe=timeframe, session=session)
    assert session.calls[0]["end"] == f"2026-11-05T{expected_end}:00Z"


def test_premarket_evaluation_never_swaps_in_yahoo_when_alpaca_fails(tmp_path, creds, monkeypatch):
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("evaluate_premarket_fail", root / "scripts" / "evaluate_premarket.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def failing(*a, **k):
        raise alpaca.AlpacaError("HTTP 500: still failing after 4 attempts")

    def no_yahoo(*a, **k):
        raise AssertionError("must not fall back to Yahoo when Alpaca keys are configured")

    monkeypatch.setattr(mod.alpaca, "load_alpaca_intraday", failing)
    monkeypatch.setattr(mod.intr, "load_yahoo_intraday", no_yahoo)
    out = tmp_path / "docs"
    assert mod.main(["--tickers", "NVDA", "--outdir", str(out), "--cache", str(tmp_path / "c")]) == 1
    assert not (out / "premarket_evaluation.md").exists()
