import numpy as np
import pytest
import pandas as pd

from monitor.evaluation import (
    block_bootstrap, evaluate, forward_excess_returns, spearman_ic, walk_forward_logit,
    evaluation_frame,
)


def test_forward_excess_alignment(synthetic):
    h = 5
    fwd = forward_excess_returns(synthetic, ["TSLA"], "SPY", h)
    c, b = synthetic["TSLA"]["Close"], synthetic["SPY"]["Close"]
    d = c.index[100]
    expected = (c.iloc[105] / c.iloc[100] - 1) - (b.loc[c.index[105]] / b.loc[d] - 1)
    assert fwd.loc[(d, "TSLA")] == expected
    assert fwd.xs("TSLA", level="ticker").iloc[-h:].isna().all()


def test_spearman_ic_perfect_and_null():
    x = pd.Series(np.arange(50.0))
    assert spearman_ic(x, x * 2) == pytest.approx(1.0)
    assert np.isnan(spearman_ic(x.iloc[:5], x.iloc[:5]))


def test_bootstrap_interval_contains_estimate(synthetic):
    frame = evaluation_frame(synthetic, ["KLAC", "TSLA"], "SPY", 5)
    est, lo, hi = block_bootstrap(frame, lambda f: f["target"].mean(), reps=200)
    assert lo <= est <= hi


def test_walk_forward_is_out_of_sample(synthetic):
    frame = evaluation_frame(synthetic, ["KLAC", "TSLA"], "SPY", 5)
    prob = walk_forward_logit(frame, min_train_days=252, refit_every=63, horizon=5)
    dates = np.array(sorted(frame.index.get_level_values("date").unique()))
    first_pred = prob.dropna().index.get_level_values("date").min()
    assert first_pred >= dates[252]
    assert prob.dropna().between(0, 1).all()


def test_evaluate_end_to_end(synthetic):
    res = evaluate(synthetic, ["SPCX", "KLAC", "ALAB", "TSLA", "VRT"], "SPY",
                   horizon=5, bootstrap_reps=100)
    assert res.n_obs > 1000
    assert -1 <= res.ic[0] <= 1
    assert set(res.ablation.index) == {"trend", "volume", "breakout", "momentum", "relative_strength"}
    assert res.walk_forward and 0 <= res.walk_forward["auc_learned"] <= 1
