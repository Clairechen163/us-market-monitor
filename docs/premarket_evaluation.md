# Does the pre-market score predict the regular session?

The [pre-market snapshot](premarket.md) describes how each stock is trading before the open.
This page tests whether that description carries information about what happens next:
**is a higher pre-market score followed by a better return from the 09:30 open to the 16:00
close, relative to SPY over the same hours?**

## Summary

*Last evaluated 2026-11-05 on 6,596 ticker-days (2023-11-07 to 2026-11-04), pre-market bars through 08:30 ET, data: alpaca-sip.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: pre-market score vs open-to-close return over SPY | -0.025 | [-0.056, +0.001] |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.06% | [-0.14%, +0.27%] |
| Rank IC: gap vs SPY alone (negative = gaps fade) | -0.010 | |

The 95% interval includes zero, so the data do not show that the pre-market score predicts the regular session. It describes the pre-market well; it is not a forecast.


## Setup

- **Universe:** ALAB, AMD, AMZN, ETN, FSLR, GOOG, MRVL, NVDA, SKHY, SPCX, TSLA; benchmark SPY.
- **Sample:** 751 trading days, 6,596 ticker-days with a full pre-market score.
  0 ticker-days with a gap larger than 40% were dropped as
  likely data errors or corporate actions.
- **Data:** Alpaca SIP feed (trades from every U.S. exchange), 30-minute bars over about 3 years, split-adjusted. Includes pre-market volume.
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
| STRONG PRICE/VOLUME | 199 | -0.17% | -0.45% | +0.13% | -0.25% | 45.7% |
| POSITIVE | 411 | +0.19% | +0.02% | +0.45% | +0.10% | 52.6% |
| WATCH | 1,050 | -0.05% | -0.23% | +0.08% | -0.03% | 48.7% |
| WEAK | 4,936 | +0.01% | -0.08% | +0.11% | -0.02% | 49.5% |

## Baselines

| signal | ic |
|---|---:|
| Pre-market score (this model) | -0.025 |
| Gap vs SPY only | -0.010 |
| Gap / ATR only | -0.008 |
| Pre-market RVOL only | +0.005 |
| Prior close end-of-day score only | -0.030 |
| Shuffled score (null) | -0.018 |

The gap rows answer a classic market-microstructure question directly: a negative IC means
pre-market moves have tended to reverse after the open (gap fade); a positive IC means they
have tended to extend (gap continuation).

## Ablation

| removed | ic | change |
|---|---:|---:|
| gap | -0.022 | +0.003 |
| volume | -0.024 | +0.002 |
| level | -0.028 | -0.003 |
| context | -0.019 | +0.006 |

A negative *change* means removing the component lowers the IC, i.e. it was contributing.

## By ticker

| ticker | n | ic | mean_gap_abs |
|---|---:|---:|---:|
| ALAB | 640 | -0.013 | 2.02% |
| AMD | 751 | +0.011 | 1.49% |
| AMZN | 751 | -0.019 | 0.79% |
| ETN | 554 | -0.070 | 1.05% |
| FSLR | 740 | -0.048 | 1.09% |
| GOOG | 751 | -0.027 | 0.78% |
| MRVL | 751 | -0.049 | 1.77% |
| NVDA | 751 | -0.067 | 1.14% |
| SKHY | 69 | +0.005 | 2.84% |
| SPCX | 87 | +0.050 | 1.41% |
| TSLA | 751 | -0.027 | 1.26% |

## Limitations

- A few years of history for a handful of stocks; SPCX and SKHY add only a few months.
- Intraday prices are not dividend-adjusted; on ex-dividend days the measured gap includes the
  dividend. The effect is small for this universe.
- Open-to-close returns ignore the cost of trading at the open, when spreads are widest.
- 11 correlated stocks; several comparisons on the same data. Not investment advice.
