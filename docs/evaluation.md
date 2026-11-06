# Does the score predict anything?

The daily monitor describes how well price, volume and trend line up today. This page
tests a stronger claim: **is a higher score at today's close followed by better
performance relative to the S&P 500 over the next 5 trading days?**

## Summary

*Last evaluated 2026-11-06 on 11,833 ticker-days (2021-12-07 to 2026-10-29), 5-day horizon, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: score vs forward return over SPY | -0.006 | [-0.053, +0.040] |
| Rank IC, non-overlapping windows only | -0.020 | |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.29% | [-0.41%, +0.88%] |
| Out-of-sample AUC: hand weights vs learned weights | 0.491 vs 0.492 | |

The 95% interval for the IC includes zero, so the data do not support a claim that the score predicts forward relative returns. That is a legitimate finding: the score is useful as a description of today's move, not as a forecast.



## Setup

- **Universe:** ALAB, AMD, AMZN, ETN, FSLR, GOOG, IBM, MRVL, NVDA, SKHY, SPCX, TSLA; benchmark SPY.
- **Sample:** 1,229 trading days, 11,833 ticker-days with a full score.
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
| STRONG PRICE/VOLUME | 925 | +0.75% | -0.03% | +1.72% | +0.25% | 52.4% |
| POSITIVE | 2,427 | +0.48% | +0.03% | +0.98% | +0.07% | 50.8% |
| WATCH | 2,410 | +0.36% | -0.11% | +0.99% | +0.09% | 50.8% |
| WEAK | 6,071 | +0.26% | -0.14% | +0.72% | +0.09% | 51.0% |

## Stability

The full-sample IC can hide periods where the relationship flips sign.

![Rolling IC](figures/rolling_ic.png)

| year | n | ic |
|---|---:|---:|
| 2021 | 162 | +0.146 |
| 2022 | 2,259 | -0.001 |
| 2023 | 2,250 | -0.102 |
| 2024 | 2,446 | +0.045 |
| 2025 | 2,500 | -0.015 |
| 2026 | 2,216 | -0.059 |

By ticker:

| ticker | n | ic | first_date |
|---|---:|---:|---:|
| ALAB | 636 | +0.107 | 2024-04-18 |
| AMD | 1,229 | +0.032 | 2021-12-07 |
| AMZN | 1,229 | -0.099 | 2021-12-07 |
| ETN | 1,229 | -0.046 | 2021-12-07 |
| FSLR | 1,229 | -0.049 | 2021-12-07 |
| GOOG | 1,229 | -0.001 | 2021-12-07 |
| IBM | 1,229 | +0.029 | 2021-12-07 |
| MRVL | 1,229 | -0.039 | 2021-12-07 |
| NVDA | 1,229 | -0.030 | 2021-12-07 |
| SKHY | 59 | -0.314 | 2026-08-07 |
| SPCX | 77 | +0.057 | 2026-07-14 |
| TSLA | 1,229 | +0.032 | 2021-12-07 |

## Baselines and ablation

A composite only earns its complexity if it beats its simplest ingredients. Each ablation row
re-scores the full history with one component removed and the rest re-weighted to 100.

![Signal comparison](figures/signal_comparison.png)

| signal | ic |
|---|---:|
| Composite score (this model) | -0.006 |
| 20-day return only (momentum) | +0.005 |
| 20-day return vs SPY only | +0.006 |
| RVOL20 only | +0.013 |
| Shuffled score (null) | -0.005 |

| removed | ic | change |
|---|---:|---:|
| trend | -0.003 | +0.003 |
| volume | -0.004 | +0.002 |
| breakout | -0.011 | -0.005 |
| momentum | -0.004 | +0.002 |
| relative_strength | -0.006 | -0.000 |

A negative *change* means removing the component hurts, i.e. it was contributing.

## Hand-chosen vs learned weights

The 25/25/20/15/15 weights were set by judgement. To check whether data would choose
differently, a logistic regression on the five component scores is refit every quarter on an
expanding window and used only to score later dates. A 5-day gap separates
each training cut-off from the test period so overlapping targets cannot leak.

Out-of-sample period: 2022-12-07 onward, 9,565 ticker-days.

| Model | AUC (target: beats SPY) | Spearman IC |
|---|---:|---:|
| Hand-weighted score | 0.491 | -0.017 |
| Walk-forward logistic regression | 0.492 | -0.031 |

Learning the weights from data does not beat the hand-chosen weights out of sample. With this little data, the simpler fixed-weight model is preferable.

## Limitations

- 12 stocks is a small, concentrated, highly correlated universe. Results may not
  generalise to other sectors or periods. Recent listings contribute only a few months of data.
- Several baselines, ablations and a model are compared on the same data. Treat any single
  small difference as noise unless it holds up out of sample.
- Yahoo Finance adjusted prices; no transaction costs, no survivorship-bias control.
- A positive IC is a statistical association, not a trading strategy and not evidence of
  institutional buying.
