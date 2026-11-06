# Does the pre-market score predict the regular session?

The [pre-market snapshot](premarket.md) describes how each stock is trading before the open.
This page tests whether that description carries information about what happens next:
**is a higher pre-market score followed by a better return from the 09:30 open to the 16:00
close, relative to SPY over the same hours?**

## Summary

*Last evaluated 2026-11-06 on 7,999 ticker-days (2023-12-27 to 2026-11-06), pre-market bars through 08:30 ET, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: pre-market score vs open-to-close return over SPY | -0.019 | [-0.052, +0.010] |
| Mean return gap: POSITIVE-or-better minus WEAK | -0.05% | [-0.23%, +0.12%] |
| Rank IC: gap vs SPY alone (negative = gaps fade) | -0.006 | |

The 95% interval includes zero, so the data do not show that the pre-market score predicts the regular session. It describes the pre-market well; it is not a forecast.


## Setup

- **Universe:** AMD, AMZN, CEG, ETN, FSLR, GOOG, IBM, MRVL, NVDA, SKHY, SPCX, TSLA, VST; benchmark SPY.
- **Sample:** 716 trading days, 7,999 ticker-days with a full pre-market score.
  0 ticker-days with a gap larger than 40% were dropped as
  likely data errors or corporate actions.
- **Data:** Yahoo Finance hourly bars over about two years. Yahoo reports no extended-hours volume, so the volume component is not scored here.
- **Snapshot time:** pre-market bars that closed by 08:30 ET, the same
  snapshot the [daily pre-market page](premarket.md) shows.
- **Target:** open-to-close return minus SPY's open-to-close return. It begins after every input is
  known, so there is no look-ahead. Daily context comes from the previous completed session.
- **Uncertainty:** one-day targets do not overlap, but stocks move together within a day, so
  intervals come from a block bootstrap over dates.

## Returns by pre-market label

![Open-to-close relative return by pre-market label](figures/premarket_label_returns.png)

| label | n | mean | ci_lo | ci_hi | median | hit_rate |
|---|---:|---:|---:|---:|---:|---:|
| STRONG PRICE/VOLUME | 245 | +0.03% | -0.35% | +0.41% | +0.07% | 51.0% |
| POSITIVE | 1,266 | -0.03% | -0.13% | +0.08% | -0.03% | 49.1% |
| WATCH | 2,313 | -0.02% | -0.10% | +0.07% | -0.03% | 48.7% |
| WEAK | 4,175 | +0.03% | -0.06% | +0.13% | -0.00% | 50.0% |

## Baselines

| signal | ic |
|---|---:|
| Pre-market score (this model) | -0.019 |
| Gap vs SPY only | -0.006 |
| Gap / ATR only | -0.006 |
| Pre-market RVOL only | n/a |
| Prior close end-of-day score only | -0.025 |
| Shuffled score (null) | +0.013 |

The gap rows answer a classic market-microstructure question directly: a negative IC means
pre-market moves have tended to reverse after the open (gap fade); a positive IC means they
have tended to extend (gap continuation).

## Ablation

| removed | ic | change |
|---|---:|---:|
| gap | -0.017 | +0.002 |
| volume | -0.019 | +0.000 |
| level | -0.027 | -0.008 |
| context | -0.008 | +0.011 |

A negative *change* means removing the component lowers the IC, i.e. it was contributing.

## By ticker

| ticker | n | ic | mean_gap_abs |
|---|---:|---:|---:|
| AMD | 714 | +0.015 | 1.45% |
| AMZN | 714 | -0.061 | 0.74% |
| CEG | 712 | -0.020 | 0.95% |
| ETN | 715 | -0.057 | 0.81% |
| FSLR | 713 | -0.046 | 1.02% |
| GOOG | 714 | -0.033 | 0.74% |
| IBM | 716 | +0.006 | 0.62% |
| MRVL | 714 | -0.039 | 1.68% |
| NVDA | 714 | -0.038 | 1.11% |
| SKHY | 64 | +0.117 | 2.76% |
| SPCX | 82 | -0.016 | 1.55% |
| TSLA | 714 | -0.054 | 1.21% |
| VST | 713 | -0.006 | 1.16% |

## Limitations

- A few years of history for a handful of stocks; SPCX and SKHY add only a few months.
- Intraday prices are not dividend-adjusted; on ex-dividend days the measured gap includes the
  dividend. The effect is small for this universe.
- Open-to-close returns ignore the cost of trading at the open, when spreads are widest.
- 13 correlated stocks; several comparisons on the same data. Not investment advice.
