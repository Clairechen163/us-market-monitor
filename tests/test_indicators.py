import numpy as np
import pandas as pd
import pytest

from monitor.indicators import (
    add_indicators, ema, prior_high, relative_volume, wilder_atr, wilder_rsi,
)


def _series(values):
    return pd.Series(values, index=pd.bdate_range("2024-01-01", periods=len(values)), dtype=float)


def test_ema_matches_recursive_definition():
    s = _series(np.arange(1, 31))
    out = ema(s, 10)
    alpha = 2 / 11
    manual = [s.iloc[0]]
    for x in s.iloc[1:]:
        manual.append(alpha * x + (1 - alpha) * manual[-1])
    assert out.iloc[:9].isna().all()
    np.testing.assert_allclose(out.iloc[9:], manual[9:])


def test_rsi_extremes_and_bounds():
    up = _series(np.arange(1, 40))
    down = _series(np.arange(40, 1, -1))
    assert wilder_rsi(up).dropna().eq(100).all()
    assert wilder_rsi(down).dropna().eq(0).all()
    rng = np.random.default_rng(1)
    noisy = wilder_rsi(_series(100 + rng.normal(0, 1, 300).cumsum())).dropna()
    assert noisy.between(0, 100).all()


def test_atr_constant_range():
    n = 40
    close = _series(np.full(n, 100.0))
    atr = wilder_atr(close + 1, close - 1, close)
    assert atr.dropna().round(10).eq(2.0).all()


def test_relative_volume_excludes_today():
    vol = _series([100.0] * 20 + [300.0])
    assert relative_volume(vol).iloc[-1] == pytest.approx(3.0)


def test_prior_high_excludes_today():
    high = _series(list(range(1, 21)) + [99])
    assert prior_high(high).iloc[-1] == 20


def test_add_indicators_columns(synthetic):
    df = add_indicators(synthetic["TSLA"], synthetic["SPY"]["Close"])
    for col in ["ema20", "ema50", "ema200", "rsi14", "atr14", "rvol20", "breakout_pct",
                "excess_5d", "excess_20d"]:
        assert col in df
    assert df["excess_5d"].notna().sum() > 0
