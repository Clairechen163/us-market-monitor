"""End-to-end: monitor -> CSV/TXT -> badges + dashboard, all offline."""

import importlib.util
from pathlib import Path

import pandas as pd

import market_monitor

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
    assert sorted(df.index) == ["ALAB", "KLAC", "SPCX", "TSLA", "VRT"]

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
