"""Technical indicators computed from daily OHLCV data.

Every indicator at row t uses only data available at the close of day t.
`tests/test_no_lookahead.py` enforces this by perturbing future rows and
checking that past values do not change.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average; NaN until `span` observations exist."""
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def wilder_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index with Wilder's smoothing (alpha = 1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - 100.0 / (1.0 + rs)
    # No losses in the window -> RSI is 100 by definition (rs = inf).
    rsi = rsi.where(avg_loss != 0, 100.0)
    return rsi.where(avg_gain.notna())


def wilder_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range with Wilder's smoothing."""
    prev_close = close.shift(1)
    true_range = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def relative_volume(volume: pd.Series, window: int = 20) -> pd.Series:
    """Today's volume divided by the mean of the *previous* `window` sessions."""
    baseline = volume.shift(1).rolling(window, min_periods=window).mean()
    return volume / baseline.replace(0, np.nan)


def prior_high(high: pd.Series, window: int = 20) -> pd.Series:
    """Highest high of the previous `window` sessions (excludes today)."""
    return high.shift(1).rolling(window, min_periods=window).max()


def add_indicators(ohlcv: pd.DataFrame, benchmark_close: pd.Series | None = None) -> pd.DataFrame:
    """Return a copy of `ohlcv` with all monitor indicators appended.

    `ohlcv` must have columns Open, High, Low, Close, Volume and a DatetimeIndex.
    `benchmark_close` (optional) enables benchmark-relative returns.
    """
    df = ohlcv.copy()
    close = df["Close"]

    df["ret_1d"] = close.pct_change(1)
    df["ret_5d"] = close.pct_change(5)
    df["ret_20d"] = close.pct_change(20)

    df["ema20"] = ema(close, 20)
    df["ema50"] = ema(close, 50)
    df["ema200"] = ema(close, 200)
    df["rsi14"] = wilder_rsi(close, 14)
    df["atr14"] = wilder_atr(df["High"], df["Low"], close, 14)
    df["atr14_pct"] = df["atr14"] / close
    df["rvol20"] = relative_volume(df["Volume"], 20)
    df["prior_high20"] = prior_high(df["High"], 20)
    df["breakout_pct"] = close / df["prior_high20"] - 1.0

    if benchmark_close is not None:
        bench = benchmark_close.reindex(df.index)
        df["excess_5d"] = df["ret_5d"] - bench.pct_change(5)
        df["excess_20d"] = df["ret_20d"] - bench.pct_change(20)
    else:
        df["excess_5d"] = np.nan
        df["excess_20d"] = np.nan

    return df
