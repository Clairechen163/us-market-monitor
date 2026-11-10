# Does the score predict anything?

The daily monitor describes how well price, volume and trend line up today. This page
tests a stronger claim: **is a higher score at today's close followed by better
performance relative to the S&P 500 over the next 5 trading days?**

## Summary

*Last evaluated 2026-11-10 on 18,557 ticker-days (2021-12-09 to 2026-11-02), 5-day horizon, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: score vs forward return over SPY | +0.002 | [-0.042, +0.034] |
| Rank IC, non-overlapping windows only | -0.004 | |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.43% | [-0.22%, +0.90%] |
| Out-of-sample AUC: hand weights vs learned weights | 0.495 vs 0.499 | |

The 95% interval for the IC includes zero, so the data do not support a claim that the score predicts forward relative returns. That is a legitimate finding: the score is useful as a description of today's move, not as a forecast.



## Setup

- **Universe:** ALAB, AMD, AMZN, BE, CEG, DELL, ETN, FSLR, GEV, GOOG, IBM, MRVL, NVDA, SKHY, SPCX, TSLA, TSM, VST; benchmark SPY.
- **Sample:** 1,229 trading days, 18,557 ticker-days with a full score.
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
| STRONG PRICE/VOLUME | 1,538 | +0.83% | +0.10% | +1.68% | +0.29% | 52.3% |
| POSITIVE | 3,835 | +0.78% | +0.31% | +1.28% | +0.27% | 52.8% |
| WATCH | 3,973 | +0.58% | +0.12% | +1.09% | +0.18% | 51.6% |
| WEAK | 9,211 | +0.37% | -0.04% | +0.84% | +0.16% | 51.6% |

## Stability

The full-sample IC can hide periods where the relationship flips sign.

![Rolling IC](figures/rolling_ic.png)

| year | n | ic |
|---|---:|---:|
| 2021 | 208 | +0.223 |
| 2022 | 3,473 | +0.016 |
| 2023 | 3,500 | -0.061 |
| 2024 | 3,876 | +0.037 |
| 2025 | 4,000 | -0.002 |
| 2026 | 3,500 | -0.053 |

By ticker:

| ticker | n | ic | first_date |
|---|---:|---:|---:|
| ALAB | 638 | +0.111 | 2024-04-18 |
| AMD | 1,229 | +0.031 | 2021-12-09 |
| AMZN | 1,229 | -0.099 | 2021-12-09 |
| BE | 1,229 | +0.029 | 2021-12-09 |
| CEG | 1,172 | +0.011 | 2022-03-03 |
| DELL | 1,229 | -0.036 | 2021-12-09 |
| ETN | 1,229 | -0.041 | 2021-12-09 |
| FSLR | 1,229 | -0.057 | 2021-12-09 |
| GEV | 630 | -0.008 | 2024-04-30 |
| GOOG | 1,229 | -0.005 | 2021-12-09 |
| IBM | 1,229 | +0.026 | 2021-12-09 |
| MRVL | 1,229 | -0.034 | 2021-12-09 |
| NVDA | 1,229 | -0.029 | 2021-12-09 |
| SKHY | 61 | -0.266 | 2026-08-07 |
| SPCX | 79 | +0.024 | 2026-07-14 |
| TSLA | 1,229 | +0.025 | 2021-12-09 |
| TSM | 1,229 | -0.010 | 2021-12-09 |
| VST | 1,229 | +0.027 | 2021-12-09 |

## Baselines and ablation

A composite only earns its complexity if it beats its simplest ingredients. Each ablation row
re-scores the full history with one component removed and the rest re-weighted to 100.

![Signal comparison](figures/signal_comparison.png)

| signal | ic |
|---|---:|
| Composite score (this model) | +0.002 |
| 20-day return only (momentum) | +0.014 |
| 20-day return vs SPY only | +0.016 |
| RVOL20 only | +0.018 |
| Shuffled score (null) | +0.010 |

| removed | ic | change |
|---|---:|---:|
| trend | +0.007 | +0.005 |
| volume | +0.002 | -0.000 |
| breakout | -0.001 | -0.003 |
| momentum | +0.002 | +0.001 |
| relative_strength | +0.000 | -0.001 |

A negative *change* means removing the component hurts, i.e. it was contributing.

## Hand-chosen vs learned weights

The 25/25/20/15/15 weights were set by judgement. To check whether data would choose
differently, a logistic regression on the five component scores is refit every quarter on an
expanding window and used only to score later dates. A 5-day gap separates
each training cut-off from the test period so overlapping targets cannot leak.

Out-of-sample period: 2022-12-09 onward, 15,086 ticker-days.

| Model | AUC (target: beats SPY) | Spearman IC |
|---|---:|---:|
| Hand-weighted score | 0.495 | -0.010 |
| Walk-forward logistic regression | 0.499 | -0.018 |

Learning the weights from data does not beat the hand-chosen weights out of sample. With this little data, the simpler fixed-weight model is preferable.

## Limitations

- 18 stocks is a small, concentrated, highly correlated universe. Results may not
  generalise to other sectors or periods. Recent listings contribute only a few months of data.
- Several baselines, ablations and a model are compared on the same data. Treat any single
  small difference as noise unless it holds up out of sample.
- Yahoo Finance adjusted prices; no transaction costs, no survivorship-bias control.
- A positive IC is a statistical association, not a trading strategy and not evidence of
  institutional buying.
