# Does the score predict anything?

The daily monitor describes how well price, volume and trend line up today. This page
tests a stronger claim: **is a higher score at today's close followed by better
performance relative to the S&P 500 over the next 5 trading days?**

## Summary

*Last evaluated 2026-11-21 on 18,615 ticker-days (2021-12-21 to 2026-11-13), 5-day horizon, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: score vs forward return over SPY | +0.002 | [-0.041, +0.035] |
| Rank IC, non-overlapping windows only | +0.002 | |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.42% | [-0.22%, +0.97%] |
| Out-of-sample AUC: hand weights vs learned weights | 0.494 vs 0.495 | |

The 95% interval for the IC includes zero, so the data do not support a claim that the score predicts forward relative returns. That is a legitimate finding: the score is useful as a description of today's move, not as a forecast.



## Setup

- **Universe:** ALAB, AMD, AMZN, BE, CEG, DELL, ETN, FSLR, GEV, GOOG, IBM, MRVL, NVDA, SKHY, SPCX, TSLA, TSM, VST; benchmark SPY.
- **Sample:** 1,230 trading days, 18,615 ticker-days with a full score.
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
| STRONG PRICE/VOLUME | 1,538 | +0.82% | +0.12% | +1.69% | +0.29% | 52.3% |
| POSITIVE | 3,834 | +0.76% | +0.26% | +1.19% | +0.26% | 52.5% |
| WATCH | 3,974 | +0.57% | +0.02% | +1.06% | +0.20% | 51.8% |
| WEAK | 9,269 | +0.35% | -0.06% | +0.82% | +0.15% | 51.5% |

## Stability

The full-sample IC can hide periods where the relationship flips sign.

![Rolling IC](figures/rolling_ic.png)

| year | n | ic |
|---|---:|---:|
| 2021 | 104 | +0.281 |
| 2022 | 3,473 | +0.018 |
| 2023 | 3,500 | -0.062 |
| 2024 | 3,876 | +0.037 |
| 2025 | 4,000 | -0.002 |
| 2026 | 3,662 | -0.046 |

By ticker:

| ticker | n | ic | first_date |
|---|---:|---:|---:|
| ALAB | 647 | +0.108 | 2024-04-18 |
| AMD | 1,230 | +0.032 | 2021-12-21 |
| AMZN | 1,230 | -0.101 | 2021-12-21 |
| BE | 1,230 | +0.028 | 2021-12-21 |
| CEG | 1,181 | +0.002 | 2022-03-03 |
| DELL | 1,230 | -0.032 | 2021-12-21 |
| ETN | 1,230 | -0.038 | 2021-12-21 |
| FSLR | 1,230 | -0.063 | 2021-12-21 |
| GEV | 639 | +0.003 | 2024-04-30 |
| GOOG | 1,230 | -0.007 | 2021-12-21 |
| IBM | 1,230 | +0.021 | 2021-12-21 |
| MRVL | 1,230 | -0.030 | 2021-12-21 |
| NVDA | 1,230 | -0.009 | 2021-12-21 |
| SKHY | 70 | -0.182 | 2026-08-07 |
| SPCX | 88 | -0.047 | 2026-07-14 |
| TSLA | 1,230 | +0.024 | 2021-12-21 |
| TSM | 1,230 | -0.009 | 2021-12-21 |
| VST | 1,230 | +0.024 | 2021-12-21 |

## Baselines and ablation

A composite only earns its complexity if it beats its simplest ingredients. Each ablation row
re-scores the full history with one component removed and the rest re-weighted to 100.

![Signal comparison](figures/signal_comparison.png)

| signal | ic |
|---|---:|
| Composite score (this model) | +0.002 |
| 20-day return only (momentum) | +0.015 |
| 20-day return vs SPY only | +0.016 |
| RVOL20 only | +0.020 |
| Shuffled score (null) | +0.003 |

| removed | ic | change |
|---|---:|---:|
| trend | +0.006 | +0.005 |
| volume | +0.002 | -0.000 |
| breakout | -0.001 | -0.003 |
| momentum | +0.003 | +0.001 |
| relative_strength | +0.001 | -0.001 |

A negative *change* means removing the component hurts, i.e. it was contributing.

## Hand-chosen vs learned weights

The 25/25/20/15/15 weights were set by judgement. To check whether data would choose
differently, a logistic regression on the five component scores is refit every quarter on an
expanding window and used only to score later dates. A 5-day gap separates
each training cut-off from the test period so overlapping targets cannot leak.

Out-of-sample period: 2022-12-21 onward, 15,136 ticker-days.

| Model | AUC (target: beats SPY) | Spearman IC |
|---|---:|---:|
| Hand-weighted score | 0.494 | -0.011 |
| Walk-forward logistic regression | 0.495 | -0.021 |

Learning the weights from data does not beat the hand-chosen weights out of sample. With this little data, the simpler fixed-weight model is preferable.

## Limitations

- 18 stocks is a small, concentrated, highly correlated universe. Results may not
  generalise to other sectors or periods. Recent listings contribute only a few months of data.
- Several baselines, ablations and a model are compared on the same data. Treat any single
  small difference as noise unless it holds up out of sample.
- Yahoo Finance adjusted prices; no transaction costs, no survivorship-bias control.
- A positive IC is a statistical association, not a trading strategy and not evidence of
  institutional buying.
