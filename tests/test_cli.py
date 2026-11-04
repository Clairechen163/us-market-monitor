"""End-to-end: monitor -> CSV/TXT -> badges + dashboard, all offline."""

import importlib.util
from pathlib import Path

import pandas as pd

import market_monitor
from monitor import config

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_monitor_and_dashboard(tmp_path):
    reports = tmp_path / "reports"
    assert market_monitor.main(["--source", "synthetic", "--outdir", str(reports)]) == 0
    csvs = list(reports.glob("market_report_*_synthetic.csv"))
    assert len(csvs) == 1 and list(reports.glob("*.txt"))
    df = pd.read_csv(csvs[0], index_col="ticker")
    assert sorted(df.index) == sorted(config.TICKERS)

    dash = _load_script("update_dashboard")
    docs = tmp_path / "docs"
    assert dash.main(["--csv", str(csvs[0]), "--outdir", str(docs)]) == 0
    for t in df.index:
        svg = (docs / "badges" / f"{t}.svg").read_text()
        assert svg.startswith("<svg") and t in svg
    assert "Latest signals" in (docs / "dashboard.md").read_text()


def test_synthetic_reports_never_feed_dashboard(tmp_path):
    (tmp_path / "market_report_20260101_synthetic.csv").write_text("ticker\n")
    dash = _load_script("update_dashboard")
    try:
        dash.latest_csv(tmp_path)
    except SystemExit:
        return
    raise AssertionError("synthetic CSV was picked up")


def test_dashboard_removes_badges_for_dropped_tickers(tmp_path):
    reports = tmp_path / "reports"
    market_monitor.main(["--source", "synthetic", "--outdir", str(reports)])
    csv = next(reports.glob("*.csv"))
    badges = tmp_path / "docs" / "badges"
    badges.mkdir(parents=True)
    (badges / "KLAC.svg").write_text("<svg/>")  # ticker no longer in the universe
    _load_script("update_dashboard").main(["--csv", str(csv), "--outdir", str(tmp_path / "docs")])
    assert not (badges / "KLAC.svg").exists()
    assert sorted(p.stem for p in badges.glob("*.svg")) == sorted(config.TICKERS)


def test_premarket_cli(tmp_path):
    import premarket_monitor

    out, docs = tmp_path / "pm", tmp_path / "docs"
    args = ["--source", "synthetic", "--outdir", str(out), "--docs", str(docs)]
    assert premarket_monitor.main([*args, "--asof", "2026-11-04 08:40"]) == 0
    df = pd.read_csv(next(out.glob("premarket_20261104_synthetic.csv")), index_col="ticker")
    assert sorted(df.index) == sorted(config.TICKERS)
    assert df["pm_score"].between(0, 100).all()
    assert "Pre-market snapshot" in (docs / "premarket.md").read_text()

    # Saturday: nothing to report, nothing written.
    assert premarket_monitor.main([*args, "--asof", "2026-11-07 08:40", "--outdir", str(tmp_path / "sat")]) == 0
    assert not (tmp_path / "sat").exists() or not list((tmp_path / "sat").glob("*.csv"))

    # Scheduled run outside the window exits quietly.
    assert premarket_monitor.main([*args, "--asof", "2026-11-04 07:40", "--window", "08:00-09:30",
                                   "--outdir", str(tmp_path / "early")]) == 0
    assert not (tmp_path / "early").exists()
