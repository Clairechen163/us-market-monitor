# Does the score predict anything?

The daily monitor describes how well price, volume and trend line up today. This page
tests a stronger claim: **is a higher score at today's close followed by better
performance relative to the S&P 500 over the next 5 trading days?**

## Summary

*Last evaluated 2026-11-04 on 9,294 ticker-days (2021-12-03 to 2026-10-27), 5-day horizon, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: score vs forward return over SPY | +0.003 | [-0.051, +0.047] |
| Rank IC, non-overlapping windows only | +0.027 | |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.47% | [-0.39%, +1.16%] |
| Out-of-sample AUC: hand weights vs learned weights | 0.493 vs 0.488 | |

The 95% interval for the IC includes zero, so the data do not support a claim that the score predicts forward relative returns. That is a legitimate finding: the score is useful as a description of today's move, not as a forecast.



## Setup

- **Universe:** ALAB, AMD, ETN, FSLR, GOOG, MRVL, NVDA, SKHY, TSLA; benchmark SPY.
- **Sample:** 1,229 trading days, 9,294 ticker-days with a full score.
  Rows labelled *INSUFFICIENT DATA* (too little history, e.g. right after an IPO) are excluded.
- **Target:** 5-day forward return minus SPY's forward return over the same days.
- **No look-ahead:** every indicator at day *t* uses data through the close of *t* only;
  this is enforced by a unit test that perturbs future prices.
- **Uncertainty:** forward windows overlap and stocks move together, so observations are not
  independent. Confidence intervals use a moving-block bootstrap that resamples 20-day blocks
  of dates, keeping both serial and cross-sectional correlation intact.

## Returns by signal label

![Forward relative return by label](figures/label_returns.png)

| label | n | mean | ci_lo | ci_hi | median | hit_rate |
|---|---:|---:|---:|---:|---:|---:|
| STRONG PRICE/VOLUME | 740 | +0.98% | +0.09% | +2.16% | +0.32% | 52.7% |
| POSITIVE | 1,806 | +0.62% | +0.02% | +1.22% | +0.04% | 50.6% |
| WATCH | 1,856 | +0.55% | -0.06% | +1.27% | +0.29% | 51.9% |
| WEAK | 4,892 | +0.26% | -0.21% | +0.81% | +0.08% | 50.8% |

## Stability

The full-sample IC can hide periods where the relationship flips sign.

![Rolling IC](figures/rolling_ic.png)

| year | n | ic |
|---|---:|---:|
| 2021 | 140 | +0.113 |
| 2022 | 1,757 | -0.006 |
| 2023 | 1,750 | -0.109 |
| 2024 | 1,942 | +0.043 |
| 2025 | 2,000 | -0.010 |
| 2026 | 1,705 | -0.032 |

By ticker:

| ticker | n | ic | first_date |
|---|---:|---:|---:|
| ALAB | 634 | +0.105 | 2024-04-18 |
| AMD | 1,229 | +0.035 | 2021-12-03 |
| ETN | 1,229 | -0.047 | 2021-12-03 |
| FSLR | 1,229 | -0.046 | 2021-12-03 |
| GOOG | 1,229 | -0.001 | 2021-12-03 |
| MRVL | 1,229 | -0.040 | 2021-12-03 |
| NVDA | 1,229 | -0.031 | 2021-12-03 |
| SKHY | 57 | -0.314 | 2026-08-07 |
| TSLA | 1,229 | +0.036 | 2021-12-03 |

## Baselines and ablation

A composite only earns its complexity if it beats its simplest ingredients. Each ablation row
re-scores the full history with one component removed and the rest re-weighted to 100.

![Signal comparison](figures/signal_comparison.png)

| signal | ic |
|---|---:|
| Composite score (this model) | +0.003 |
| 20-day return only (momentum) | +0.013 |
| 20-day return vs SPY only | +0.014 |
| RVOL20 only | +0.014 |
| Shuffled score (null) | -0.006 |

| removed | ic | change |
|---|---:|---:|
| trend | +0.001 | -0.001 |
| volume | +0.006 | +0.003 |
| breakout | -0.001 | -0.004 |
| momentum | +0.005 | +0.002 |
| relative_strength | +0.002 | -0.000 |

A negative *change* means removing the component hurts, i.e. it was contributing.

## Hand-chosen vs learned weights

The 25/25/20/15/15 weights were set by judgement. To check whether data would choose
differently, a logistic regression on the five component scores is refit every quarter on an
expanding window and used only to score later dates. A 5-day gap separates
each training cut-off from the test period so overlapping targets cannot leak.

Out-of-sample period: 2022-12-05 onward, 7,530 ticker-days.

| Model | AUC (target: beats SPY) | Spearman IC |
|---|---:|---:|
| Hand-weighted score | 0.493 | -0.009 |
| Walk-forward logistic regression | 0.488 | -0.036 |

Learning the weights from data does not beat the hand-chosen weights out of sample. With this little data, the simpler fixed-weight model is preferable.

## Limitations

- 9 stocks is a small, concentrated, highly correlated universe. Results may not
  generalise to other sectors or periods. Recent listings contribute only a few months of data.
- Several baselines, ablations and a model are compared on the same data. Treat any single
  small difference as noise unless it holds up out of sample.
- Yahoo Finance adjusted prices; no transaction costs, no survivorship-bias control.
- A positive IC is a statistical association, not a trading strategy and not evidence of
  institutional buying.
