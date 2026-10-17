import numpy as np
import pandas as pd

from monitor.config import INSUFFICIENT_LABEL, WEIGHTS
from monitor.indicators import add_indicators
from monitor.pipeline import build_panel, latest_snapshot
from monitor.scoring import label_for, score_frame


def test_weights_sum_to_100():
    assert sum(WEIGHTS.values()) == 100


def test_scores_bounded_and_labelled(synthetic):
    panel = build_panel(synthetic, ["KLAC", "TSLA", "VRT"], "SPY")
    s = panel["score"].dropna()
    assert len(s) > 1000
    assert s.between(0, 100).all()
    assert set(panel["label"]) <= {"STRONG PRICE/VOLUME", "POSITIVE", "WATCH", "WEAK", INSUFFICIENT_LABEL}


def test_label_thresholds():
    assert label_for(75.0, 1.0) == "STRONG PRICE/VOLUME"
    assert label_for(74.9, 1.0) == "POSITIVE"
    assert label_for(60.0, 1.0) == "POSITIVE"
    assert label_for(45.0, 1.0) == "WATCH"
    assert label_for(44.9, 1.0) == "WEAK"
    assert label_for(90.0, 0.3) == INSUFFICIENT_LABEL
    assert label_for(float("nan"), 1.0) == INSUFFICIENT_LABEL


def test_young_listing_is_renormalised_not_zeroed(synthetic):
    # SPCX in the fixture has 120 sessions: no EMA200 yet.
    ind = add_indicators(synthetic["SPCX"], synthetic["SPY"]["Close"])
    last = score_frame(ind).iloc[-1]
    assert ind["ema200"].isna().all()
    assert 0.85 < last["coverage"] < 1.0
    assert last["label"] != INSUFFICIENT_LABEL


def test_ideal_setup_scores_high():
    row = pd.DataFrame({
        "Close": [110.0], "ema20": [105.0], "ema50": [100.0], "ema200": [90.0],
        "rvol20": [2.5], "ret_1d": [0.04], "breakout_pct": [0.03], "rsi14": [65.0],
        "ret_5d": [0.08], "ret_20d": [0.15], "excess_5d": [0.06], "excess_20d": [0.12],
    })
    out = score_frame(row).iloc[0]
    assert out["score"] >= 95
    assert out["label"] == "STRONG PRICE/VOLUME"


def test_high_volume_selloff_is_not_confirmation():
    base = dict(Close=[100.0], ema20=[101.0], ema50=[102.0], ema200=[95.0], breakout_pct=[-0.04],
                rsi14=[45.0], ret_5d=[-0.03], ret_20d=[-0.02], excess_5d=[np.nan], excess_20d=[np.nan])
    up = score_frame(pd.DataFrame({**base, "rvol20": [2.5], "ret_1d": [0.03]}))["pts_volume"].iloc[0]
    down = score_frame(pd.DataFrame({**base, "rvol20": [2.5], "ret_1d": [-0.03]}))["pts_volume"].iloc[0]
    assert down < up / 2


def test_ablation_renormalises(synthetic):
    panel = build_panel(synthetic, ["TSLA"], "SPY", exclude=("volume",))
    assert "pts_volume" not in panel
    assert panel["score"].dropna().between(0, 100).all()


def test_latest_snapshot_one_row_per_ticker(synthetic):
    snap = latest_snapshot(build_panel(synthetic, ["KLAC", "TSLA", "SPCX"], "SPY"))
    assert sorted(snap.index) == ["KLAC", "SPCX", "TSLA"]
