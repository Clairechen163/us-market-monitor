# Does the pre-market score predict the regular session?

The [pre-market snapshot](premarket.md) describes how each stock is trading before the open.
This page tests whether that description carries information about what happens next:
**is a higher pre-market score followed by a better return from the 09:30 open to the 16:00
close, relative to SPY over the same hours?**

## Summary

*Last evaluated 2026-11-07 on 9,356 ticker-days (2023-11-08 to 2026-11-06), pre-market bars through 08:30 ET, data: alpaca-sip.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: pre-market score vs open-to-close return over SPY | -0.022 | [-0.052, +0.002] |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.04% | [-0.17%, +0.25%] |
| Rank IC: gap vs SPY alone (negative = gaps fade) | -0.016 | |

The 95% interval includes zero, so the data do not show that the pre-market score predicts the regular session. It describes the pre-market well; it is not a forecast.


## Setup

- **Universe:** ALAB, AMD, AMZN, CEG, ETN, FSLR, GEV, GOOG, IBM, MRVL, NVDA, SKHY, SPCX, TSLA, VST; benchmark SPY.
- **Sample:** 752 trading days, 9,356 ticker-days with a full pre-market score.
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
| STRONG PRICE/VOLUME | 301 | +0.10% | -0.20% | +0.46% | -0.07% | 48.5% |
| POSITIVE | 595 | +0.05% | -0.11% | +0.26% | +0.05% | 51.3% |
| WATCH | 1,552 | -0.08% | -0.22% | +0.04% | -0.04% | 48.8% |
| WEAK | 6,908 | +0.03% | -0.04% | +0.12% | -0.01% | 49.7% |

## Baselines

| signal | ic |
|---|---:|
| Pre-market score (this model) | -0.022 |
| Gap vs SPY only | -0.016 |
| Gap / ATR only | -0.014 |
| Pre-market RVOL only | +0.007 |
| Prior close end-of-day score only | -0.021 |
| Shuffled score (null) | -0.002 |

The gap rows answer a classic market-microstructure question directly: a negative IC means
pre-market moves have tended to reverse after the open (gap fade); a positive IC means they
have tended to extend (gap continuation).

## Ablation

| removed | ic | change |
|---|---:|---:|
| gap | -0.018 | +0.004 |
| volume | -0.018 | +0.004 |
| level | -0.027 | -0.005 |
| context | -0.017 | +0.005 |

A negative *change* means removing the component lowers the IC, i.e. it was contributing.

## By ticker

| ticker | n | ic | mean_gap_abs |
|---|---:|---:|---:|
| ALAB | 642 | -0.010 | 2.04% |
| AMD | 752 | +0.015 | 1.51% |
| AMZN | 752 | -0.020 | 0.80% |
| CEG | 677 | -0.015 | 1.08% |
| ETN | 556 | -0.072 | 1.06% |
| FSLR | 741 | -0.043 | 1.09% |
| GEV | 630 | -0.082 | 1.22% |
| GOOG | 752 | -0.028 | 0.78% |
| IBM | 737 | +0.000 | 0.64% |
| MRVL | 752 | -0.048 | 1.79% |
| NVDA | 752 | -0.066 | 1.15% |
| SKHY | 71 | +0.025 | 2.93% |
| SPCX | 89 | +0.077 | 1.47% |
| TSLA | 752 | -0.025 | 1.26% |
| VST | 701 | -0.019 | 1.30% |

## Limitations

- A few years of history for a handful of stocks; SPCX and SKHY add only a few months.
- Intraday prices are not dividend-adjusted; on ex-dividend days the measured gap includes the
  dividend. The effect is small for this universe.
- Open-to-close returns ignore the cost of trading at the open, when spreads are widest.
- 15 correlated stocks; several comparisons on the same data. Not investment advice.
