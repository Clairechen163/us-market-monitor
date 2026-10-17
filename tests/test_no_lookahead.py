"""Changing future prices must never change past indicators or scores."""

import numpy as np
import pandas as pd

from monitor.pipeline import build_panel

CHECK_COLS = ["ema20", "ema50", "ema200", "rsi14", "atr14", "rvol20", "breakout_pct",
              "excess_5d", "excess_20d", "score", "coverage"]


def test_future_shock_does_not_leak(synthetic):
    tickers = ["KLAC", "TSLA"]
    cutoff = synthetic["TSLA"].index[-60]

    shocked = {t: f.copy() for t, f in synthetic.items()}
    for t in [*tickers, "SPY"]:
        future = shocked[t].index > cutoff
        shocked[t].loc[future, ["Open", "High", "Low", "Close"]] *= 3.0
        shocked[t].loc[future, "Volume"] *= 10.0

    a = build_panel(synthetic, tickers, "SPY")
    b = build_panel(shocked, tickers, "SPY")
    past = a.index.get_level_values("date") <= cutoff
    pd.testing.assert_frame_equal(a.loc[past, CHECK_COLS], b.loc[past, CHECK_COLS])
    # Sanity: the shock did change the future.
    assert not np.allclose(a.loc[~past, "Close"], b.loc[~past, "Close"])
