"""Does the pre-market score predict the regular session?

Question: is a higher pre-market score at clock time C (default 09:00 ET)
followed by a better open-to-close return relative to SPY that same day?

The target starts at the 09:30 open, after every input is known, so there is
no look-ahead. The target is one day long, so windows do not overlap; stocks
are still correlated within a day, so confidence intervals use a block
bootstrap over dates (10-day blocks).

The same question is asked of each ingredient alone. The gap baseline
matters in particular: a negative IC means pre-market gaps tend to *fade*
during the regular session, a positive IC that they *continue*.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

import numpy as np
import pandas as pd

from .config import BENCHMARK, INSUFFICIENT_LABEL, MAX_PLAUSIBLE_GAP
from .evaluation import _label_table, _spread, block_bootstrap, spearman_ic
from .premarket import COMPONENTS, premarket_features, score_premarket


@dataclass
class PremarketResult:
    cutoff: time
    n_obs: int
    n_dates: int
    n_dropped_gaps: int
    start: pd.Timestamp
    end: pd.Timestamp
    tickers: list[str]
    ic: tuple[float, float, float]
    spread: tuple[float, float, float]
    by_label: pd.DataFrame
    by_ticker: pd.DataFrame
    baselines: pd.DataFrame
    ablation: pd.DataFrame


def premarket_eval_frame(intraday, daily, tickers, benchmark=BENCHMARK, cutoff=time(9, 0)):
    feats = premarket_features(intraday, daily, tickers, benchmark, cutoff=cutoff)
    feats = feats.join(score_premarket(feats))
    usable = feats["pm_label"].ne(INSUFFICIENT_LABEL) & feats["target"].notna() & feats["pm_score"].notna()
    implausible = feats["gap"].abs() > MAX_PLAUSIBLE_GAP
    frame = feats[usable & ~implausible].copy()
    frame["score"], frame["label"] = frame["pm_score"], frame["pm_label"]
    return frame, int((usable & implausible).sum()), feats


def evaluate_premarket(intraday, daily, tickers, benchmark=BENCHMARK, cutoff=time(9, 0),
                       reps: int = 1000, seed: int = 0) -> PremarketResult:
    frame, dropped, feats = premarket_eval_frame(intraday, daily, tickers, benchmark, cutoff)
    if len(frame) < 100:
        raise RuntimeError(f"only {len(frame)} usable pre-market observations; need at least 100")
    dates = frame.index.get_level_values("date")

    ic = block_bootstrap(frame, lambda f: spearman_ic(f["score"], f["target"]), block=10, reps=reps, seed=seed)
    spread = block_bootstrap(frame, _spread, block=10, reps=reps, seed=seed)

    rng = np.random.default_rng(seed)
    shuffled = pd.Series(rng.permutation(frame["score"].to_numpy()), index=frame.index)
    baselines = pd.DataFrame([
        {"signal": "Pre-market score (this model)", "ic": ic[0]},
        {"signal": "Gap vs SPY only", "ic": spearman_ic(frame["excess_gap"], frame["target"])},
        {"signal": "Gap / ATR only", "ic": spearman_ic(frame["gap_atr"], frame["target"])},
        {"signal": "Pre-market RVOL only", "ic": spearman_ic(frame["pm_rvol"], frame["target"])},
        {"signal": "Prior close end-of-day score only", "ic": spearman_ic(frame["ctx_score"], frame["target"])},
        {"signal": "Shuffled score (null)", "ic": spearman_ic(shuffled, frame["target"])},
    ]).set_index("signal")

    rows = []
    for comp in COMPONENTS:
        reduced = score_premarket(feats, exclude=(comp,))["pm_score"].reindex(frame.index)
        r_ic = spearman_ic(reduced, frame["target"])
        rows.append({"removed": comp, "ic": r_ic, "change": r_ic - ic[0]})
    ablation = pd.DataFrame(rows).set_index("removed")

    by_ticker = pd.DataFrame([
        {"ticker": t, "n": len(g), "ic": spearman_ic(g["score"], g["target"]),
         "mean_gap_abs": g["gap"].abs().mean()}
        for t, g in frame.groupby(level="ticker")
    ]).set_index("ticker")

    unique = np.array(sorted(dates.unique()))
    return PremarketResult(
        cutoff=cutoff, n_obs=len(frame), n_dates=len(unique), n_dropped_gaps=dropped,
        start=unique[0], end=unique[-1], tickers=sorted(by_ticker.index),
        ic=ic, spread=spread, by_label=_label_table(frame), by_ticker=by_ticker,
        baselines=baselines, ablation=ablation,
    )
