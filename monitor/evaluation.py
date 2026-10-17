"""Does the score carry information about what happens next?

The daily monitor is descriptive. This module asks the empirical question a
data scientist should ask before trusting it:

    Is a higher score at the close of day t associated with a higher
    benchmark-relative return over days t+1 ... t+h?

Methods
-------
* Target: h-day forward return in excess of SPY (default h = 5).
* Rank information coefficient (Spearman IC) between score and target,
  pooled and per ticker.
* Mean target by signal label, with a moving-block bootstrap over dates for
  confidence intervals (forward windows overlap, so i.i.d. resampling would
  understate uncertainty).
* Robustness: non-overlapping subsample, IC by calendar year.
* Baselines: simple 20-day momentum and a shuffled score.
* Ablation: re-score with each component removed.
* Walk-forward model: logistic regression on the component scores, refit on
  an expanding window and evaluated only on later, unseen dates. This tests
  whether the hand-chosen weights leave predictive information on the table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from .config import INSUFFICIENT_LABEL, LABELS, WEIGHTS
from .pipeline import build_panel
from .scoring import COMPONENTS

LABEL_ORDER = [lab for _, lab in LABELS]


# --------------------------------------------------------------------------- data
def forward_excess_returns(
    data: dict[str, pd.DataFrame], tickers: list[str], benchmark: str | None, horizon: int
) -> pd.Series:
    bench_fwd = None
    if benchmark and benchmark in data:
        b = data[benchmark]["Close"]
        bench_fwd = b.shift(-horizon) / b - 1.0
    pieces = []
    for t in tickers:
        if t not in data:
            continue
        c = data[t]["Close"]
        fwd = c.shift(-horizon) / c - 1.0
        if bench_fwd is not None:
            fwd = fwd - bench_fwd.reindex(fwd.index)
        pieces.append(pd.DataFrame({"date": fwd.index, "ticker": t, "fwd": fwd.to_numpy()}))
    out = pd.concat(pieces).set_index(["date", "ticker"])["fwd"]
    return out.rename(f"fwd_excess_{horizon}d")


def evaluation_frame(
    data: dict[str, pd.DataFrame], tickers: list[str], benchmark: str | None, horizon: int
) -> pd.DataFrame:
    panel = build_panel(data, tickers, benchmark)
    panel["target"] = forward_excess_returns(data, tickers, benchmark, horizon)
    ok = panel["label"].ne(INSUFFICIENT_LABEL) & panel["target"].notna() & panel["score"].notna()
    return panel[ok].copy()


# ------------------------------------------------------------------- statistics
def spearman_ic(x: pd.Series, y: pd.Series) -> float:
    mask = x.notna() & y.notna()
    if mask.sum() < 10 or x[mask].nunique() < 2:
        return float("nan")
    return float(spearmanr(x[mask], y[mask]).statistic)


def block_bootstrap(
    frame: pd.DataFrame,
    stat,
    block: int = 20,
    reps: int = 1000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Moving-block bootstrap over trading dates. Returns (estimate, lo95, hi95)."""
    rng = np.random.default_rng(seed)
    dates = frame.index.get_level_values("date")
    unique = np.array(sorted(dates.unique()))
    n = len(unique)
    positions = pd.Series(np.arange(len(frame))).groupby(
        pd.Index(dates).map({d: i for i, d in enumerate(unique)}).to_numpy()
    ).apply(np.array)
    estimate = stat(frame)
    if n < 2 * block:
        return estimate, float("nan"), float("nan")
    n_blocks = int(np.ceil(n / block))
    draws = []
    for _ in range(reps):
        starts = rng.integers(0, n - block + 1, n_blocks)
        date_ids = (starts[:, None] + np.arange(block)).ravel()[:n]
        rows = np.concatenate([positions[i] for i in date_ids])
        value = stat(frame.iloc[rows])
        if np.isfinite(value):
            draws.append(value)
    if len(draws) < reps // 2:
        return estimate, float("nan"), float("nan")
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return estimate, float(lo), float(hi)


# --------------------------------------------------------------- walk-forward
def component_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Each component as a fraction of its maximum; missing -> 0.5 + flag."""
    feats = pd.DataFrame(index=frame.index)
    for c in COMPONENTS:
        frac = frame[f"pts_{c}"] / WEIGHTS[c]
        feats[c] = frac.fillna(0.5)
        feats[f"{c}_missing"] = frac.isna().astype(float)
    return feats.loc[:, feats.std() > 0]


def walk_forward_logit(
    frame: pd.DataFrame, min_train_days: int = 252, refit_every: int = 63, horizon: int = 5
) -> pd.Series:
    """Out-of-sample probability that the forward excess return is positive.

    A gap of `horizon` days between the training cut-off and the first test
    date prevents overlapping forward windows from leaking labels.
    """
    X_all = component_features(frame)
    y_all = (frame["target"] > 0).astype(int)
    dates = np.array(sorted(frame.index.get_level_values("date").unique()))
    preds = pd.Series(np.nan, index=frame.index)
    row_dates = frame.index.get_level_values("date")

    for start in range(min_train_days, len(dates), refit_every):
        train_end = dates[start - horizon - 1]
        test_dates = dates[start : start + refit_every]
        train = row_dates <= train_end
        test = row_dates.isin(test_dates)
        if y_all[train].nunique() < 2:
            continue
        model = LogisticRegression(C=1.0, max_iter=1000)
        model.fit(X_all[train], y_all[train])
        preds[test] = model.predict_proba(X_all[test])[:, 1]
    return preds


# ---------------------------------------------------------------------- report
@dataclass
class EvaluationResult:
    horizon: int
    n_obs: int
    n_dates: int
    start: pd.Timestamp
    end: pd.Timestamp
    tickers: list[str]
    ic: tuple[float, float, float]
    ic_nonoverlap: float
    spread: tuple[float, float, float]
    by_label: pd.DataFrame
    by_ticker: pd.DataFrame
    by_year: pd.DataFrame
    baselines: pd.DataFrame
    ablation: pd.DataFrame
    walk_forward: dict = field(default_factory=dict)
    rolling_ic: pd.Series | None = None


def _label_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lab in LABEL_ORDER:
        sub = frame[frame["label"] == lab]
        if sub.empty:
            rows.append({"label": lab, "n": 0})
            continue
        est, lo, hi = block_bootstrap(sub, lambda f: f["target"].mean(), reps=500)
        rows.append({
            "label": lab, "n": len(sub), "mean": est, "ci_lo": lo, "ci_hi": hi,
            "median": sub["target"].median(), "hit_rate": (sub["target"] > 0).mean(),
        })
    return pd.DataFrame(rows).set_index("label")


def _spread(f: pd.DataFrame) -> float:
    top = f.loc[f["label"].isin(LABEL_ORDER[:2]), "target"]
    bottom = f.loc[f["label"] == LABEL_ORDER[-1], "target"]
    if len(top) < 5 or len(bottom) < 5:
        return float("nan")
    return float(top.mean() - bottom.mean())


def evaluate(
    data: dict[str, pd.DataFrame],
    tickers: list[str],
    benchmark: str | None,
    horizon: int = 5,
    bootstrap_reps: int = 1000,
    seed: int = 0,
) -> EvaluationResult:
    frame = evaluation_frame(data, tickers, benchmark, horizon)
    if len(frame) < 100:
        raise RuntimeError(f"only {len(frame)} usable observations; need at least 100")
    dates = frame.index.get_level_values("date")

    ic = block_bootstrap(frame, lambda f: spearman_ic(f["score"], f["target"]),
                         reps=bootstrap_reps, seed=seed)
    spread = block_bootstrap(frame, _spread, reps=bootstrap_reps, seed=seed)

    unique = np.array(sorted(dates.unique()))
    nonoverlap = frame[dates.isin(unique[::horizon])]
    ic_nonoverlap = spearman_ic(nonoverlap["score"], nonoverlap["target"])

    by_ticker = pd.DataFrame([
        {"ticker": t, "n": len(g), "ic": spearman_ic(g["score"], g["target"]),
         "first_date": g.index.get_level_values("date").min().date()}
        for t, g in frame.groupby(level="ticker")
    ]).set_index("ticker")

    by_year = pd.DataFrame([
        {"year": int(y), "n": len(g), "ic": spearman_ic(g["score"], g["target"])}
        for y, g in frame.groupby(dates.year)
    ]).set_index("year")

    rng = np.random.default_rng(seed)
    shuffled = pd.Series(rng.permutation(frame["score"].to_numpy()), index=frame.index)
    baselines = pd.DataFrame([
        {"signal": "Composite score (this model)", "ic": ic[0]},
        {"signal": "20-day return only (momentum)", "ic": spearman_ic(frame["ret_20d"], frame["target"])},
        {"signal": "20-day return vs SPY only", "ic": spearman_ic(frame["excess_20d"], frame["target"])},
        {"signal": "RVOL20 only", "ic": spearman_ic(frame["rvol20"], frame["target"])},
        {"signal": "Shuffled score (null)", "ic": spearman_ic(shuffled, frame["target"])},
    ]).set_index("signal")

    abl_rows = []
    for comp in COMPONENTS:
        reduced = build_panel(data, tickers, benchmark, exclude=(comp,))["score"]
        r = reduced.reindex(frame.index)
        abl_ic = spearman_ic(r, frame["target"])
        abl_rows.append({"removed": comp, "ic": abl_ic, "change": abl_ic - ic[0]})
    ablation = pd.DataFrame(abl_rows).set_index("removed")

    wf = {}
    prob = walk_forward_logit(frame, horizon=horizon)
    oos = prob.notna()
    if oos.sum() > 50 and frame.loc[oos, "target"].gt(0).nunique() == 2:
        y = (frame.loc[oos, "target"] > 0).astype(int)
        wf = {
            "n_oos": int(oos.sum()),
            "oos_start": frame[oos].index.get_level_values("date").min().date(),
            "auc_learned": roc_auc_score(y, prob[oos]),
            "auc_hand": roc_auc_score(y, frame.loc[oos, "score"]),
            "ic_learned": spearman_ic(prob[oos], frame.loc[oos, "target"]),
            "ic_hand": spearman_ic(frame.loc[oos, "score"], frame.loc[oos, "target"]),
        }

    # Trailing ~6-month pooled IC, sampled weekly, to show stability over time.
    flat = frame.reset_index()
    rolling = {}
    for d in unique[125::5]:
        window = flat[(flat["date"] > d - pd.Timedelta(days=182)) & (flat["date"] <= d)]
        rolling[d] = spearman_ic(window["score"], window["target"])
    rolling_ic = pd.Series(rolling, dtype=float).dropna()

    return EvaluationResult(
        horizon=horizon, n_obs=len(frame), n_dates=len(unique),
        start=unique[0], end=unique[-1], tickers=sorted(by_ticker.index),
        ic=ic, ic_nonoverlap=ic_nonoverlap, spread=spread,
        by_label=_label_table(frame), by_ticker=by_ticker, by_year=by_year,
        baselines=baselines, ablation=ablation, walk_forward=wf, rolling_ic=rolling_ic,
    )
