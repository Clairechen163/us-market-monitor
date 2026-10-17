"""Transparent 0-100 price/volume alignment score.

Design choices
--------------
* Components use smooth piecewise-linear maps instead of hard cut-offs, so a
  tiny change in an input cannot flip many points at once.
* Missing inputs (e.g. no EMA200 for a recent IPO) are not silently scored as
  zero. The score is re-normalised over the inputs that exist, and the share
  of weight that could be computed is reported as `coverage`. Rows below
  `MIN_COVERAGE` are labelled INSUFFICIENT DATA.
* Relative strength uses returns in excess of the benchmark (SPY) when it is
  available and falls back to absolute returns otherwise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import INSUFFICIENT_LABEL, LABELS, MIN_COVERAGE, WEIGHTS

COMPONENTS = list(WEIGHTS)


def _interp(x: pd.Series, xp: list[float], fp: list[float]) -> pd.Series:
    values = np.interp(x.to_numpy(dtype=float), xp, fp)
    return pd.Series(values, index=x.index).where(x.notna())


def _weighted_parts(parts: list[tuple[pd.Series, float]]) -> tuple[pd.Series, pd.Series]:
    """Combine sub-signals given as (fraction in [0,1] or NaN, weight).

    Returns (points earned, weight available) per row.
    """
    earned = sum(frac.fillna(0.0) * w for frac, w in parts)
    available = sum(frac.notna().astype(float) * w for frac, w in parts)
    return earned, available


def trend_component(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    w = WEIGHTS["trend"]

    def above(a: str, b: str) -> pd.Series:
        return (df[a] > df[b]).astype(float).where(df[a].notna() & df[b].notna())

    return _weighted_parts(
        [
            (above("Close", "ema20"), w * 0.32),
            (above("ema20", "ema50"), w * 0.32),
            (above("Close", "ema200"), w * 0.36),
        ]
    )


def volume_component(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    # RVOL 0.5 -> 0, 1.0 -> 40%, 1.5 -> 72%, >= 2.0 -> 100%
    frac = _interp(df["rvol20"], [0.5, 1.0, 1.5, 2.0], [0.0, 0.40, 0.72, 1.0])
    # High volume on a down day is distribution, not confirmation.
    frac = frac.where(~(df["ret_1d"] < 0), frac * 0.25)
    return _weighted_parts([(frac, WEIGHTS["volume"])])


def breakout_component(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    # 10% below the prior 20-day high -> 0, at the high -> 70%, 3% above -> 100%
    frac = _interp(df["breakout_pct"], [-0.10, -0.05, 0.0, 0.03], [0.0, 0.30, 0.70, 1.0])
    return _weighted_parts([(frac, WEIGHTS["breakout"])])


def momentum_component(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    # Rewards 55-70; fades when overbought (>75) or weak (<45).
    frac = _interp(
        df["rsi14"], [30, 45, 55, 70, 80, 90], [0.0, 0.35, 0.85, 1.0, 0.65, 0.30]
    )
    return _weighted_parts([(frac, WEIGHTS["momentum"])])


def relative_strength_component(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    w = WEIGHTS["relative_strength"]
    r5 = df["excess_5d"].where(df["excess_5d"].notna(), df["ret_5d"])
    r20 = df["excess_20d"].where(df["excess_20d"].notna(), df["ret_20d"])
    # -5% -> 0, 0 -> 50%, +5% -> 100% (5d); twice as wide for 20d.
    f5 = _interp(r5, [-0.05, 0.0, 0.05], [0.0, 0.5, 1.0])
    f20 = _interp(r20, [-0.10, 0.0, 0.10], [0.0, 0.5, 1.0])
    return _weighted_parts([(f5, w * 0.4), (f20, w * 0.6)])


_COMPONENT_FUNCS = {
    "trend": trend_component,
    "volume": volume_component,
    "breakout": breakout_component,
    "momentum": momentum_component,
    "relative_strength": relative_strength_component,
}


def label_for(score: float, coverage: float) -> str:
    if not np.isfinite(score) or coverage < MIN_COVERAGE:
        return INSUFFICIENT_LABEL
    for threshold, label in LABELS:
        if score >= threshold:
            return label
    return LABELS[-1][1]


def score_frame(df: pd.DataFrame, exclude: tuple[str, ...] = ()) -> pd.DataFrame:
    """Score every row of an indicator frame.

    `exclude` drops components entirely (used for ablation studies); the
    remaining weights are re-normalised to 100.
    """
    out = pd.DataFrame(index=df.index)
    earned_total = pd.Series(0.0, index=df.index)
    available_total = pd.Series(0.0, index=df.index)
    possible_total = 0.0

    for name in COMPONENTS:
        if name in exclude:
            continue
        earned, available = _COMPONENT_FUNCS[name](df)
        out[f"pts_{name}"] = earned.where(available > 0)
        earned_total += earned
        available_total += available
        possible_total += WEIGHTS[name]

    out["coverage"] = available_total / possible_total
    out["score"] = (100.0 * earned_total / available_total.replace(0, np.nan)).round(1)
    out["label"] = [label_for(s, c) for s, c in zip(out["score"], out["coverage"])]
    return out
