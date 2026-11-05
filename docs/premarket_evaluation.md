# Does the pre-market score predict the regular session?

The [pre-market snapshot](premarket.md) describes how each stock is trading before the open.
This page tests whether that description carries information about what happens next:
**is a higher pre-market score followed by a better return from the 09:30 open to the 16:00
close, relative to SPY over the same hours?**

## Summary

*Last evaluated 2026-11-05 on 5,864 ticker-days (2023-12-26 to 2026-11-04), pre-market bars through 09:00 ET, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: pre-market score vs open-to-close return over SPY | -0.030 | [-0.066, +0.002] |
| Mean return gap: POSITIVE-or-better minus WEAK | -0.08% | [-0.28%, +0.11%] |
| Rank IC: gap vs SPY alone (negative = gaps fade) | +0.000 | |

The 95% interval includes zero, so the data do not show that the pre-market score predicts the regular session. It describes the pre-market well; it is not a forecast.


## Setup

- **Universe:** AMD, AMZN, ETN, FSLR, GOOG, MRVL, NVDA, SKHY, SPCX, TSLA; benchmark SPY.
- **Sample:** 717 trading days, 5,864 ticker-days with a full pre-market score.
  0 ticker-days with a gap larger than 40% were dropped as
  likely data errors or corporate actions.
- **Snapshot time:** pre-market bars that closed by 09:00 ET. Yahoo keeps
  extended-hours history only at hourly resolution beyond ~60 days, so the evaluation uses hourly
  bars; the live monitor uses 5-minute bars and runs at ~08:40 ET.
- **Target:** open-to-close return minus SPY's open-to-close return. It begins after every input is
  known, so there is no look-ahead. Daily context comes from the previous completed session.
- **Uncertainty:** one-day targets do not overlap, but stocks move together within a day, so
  intervals come from a block bootstrap over dates.

## Returns by pre-market label

![Open-to-close relative return by pre-market label](figures/premarket_label_returns.png)

| label | n | mean | ci_lo | ci_hi | median | hit_rate |
|---|---:|---:|---:|---:|---:|---:|
| STRONG PRICE/VOLUME | 194 | -0.11% | -0.46% | +0.20% | +0.03% | 50.5% |
| POSITIVE | 847 | -0.04% | -0.20% | +0.08% | -0.03% | 48.8% |
| WATCH | 1,736 | +0.00% | -0.10% | +0.10% | -0.06% | 48.7% |
| WEAK | 3,087 | +0.03% | -0.08% | +0.14% | +0.00% | 50.0% |

## Baselines

| signal | ic |
|---|---:|
| Pre-market score (this model) | -0.030 |
| Gap vs SPY only | +0.000 |
| Gap / ATR only | +0.001 |
| Pre-market RVOL only | n/a |
| Prior close end-of-day score only | -0.038 |
| Shuffled score (null) | +0.006 |

The gap rows answer a classic market-microstructure question directly: a negative IC means
pre-market moves have tended to reverse after the open (gap fade); a positive IC means they
have tended to extend (gap continuation).

## Ablation

| removed | ic | change |
|---|---:|---:|
| gap | -0.030 | -0.001 |
| volume | -0.030 | +0.000 |
| level | -0.034 | -0.004 |
| context | -0.015 | +0.014 |

A negative *change* means removing the component lowers the IC, i.e. it was contributing.

## By ticker

| ticker | n | ic | mean_gap_abs |
|---|---:|---:|---:|
| AMD | 715 | +0.008 | 1.54% |
| AMZN | 715 | -0.053 | 0.81% |
| ETN | 717 | -0.059 | 0.92% |
| FSLR | 715 | -0.041 | 1.09% |
| GOOG | 715 | -0.033 | 0.79% |
| MRVL | 715 | -0.035 | 1.83% |
| NVDA | 715 | -0.047 | 1.17% |
| SKHY | 62 | +0.075 | 2.71% |
| SPCX | 80 | -0.046 | 1.46% |
| TSLA | 715 | -0.055 | 1.28% |

## Limitations

- About two years of hourly extended-hours data from Yahoo Finance, an unofficial source.
  Extended-hours volume is sometimes missing; when it is, the volume component is left out and
  the score re-normalised (see *coverage*).
- Intraday prices are not dividend-adjusted; on ex-dividend days the measured gap includes the
  dividend. The effect is small for this universe.
- Open-to-close returns ignore the cost of trading at the open, when spreads are widest.
- 10 correlated stocks; several comparisons on the same data. Not investment advice.
