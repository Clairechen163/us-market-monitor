# Does the pre-market score predict the regular session?

The [pre-market snapshot](premarket.md) describes how each stock is trading before the open.
This page tests whether that description carries information about what happens next:
**is a higher pre-market score followed by a better return from the 09:30 open to the 16:00
close, relative to SPY over the same hours?**

## Summary

*Last evaluated 2026-11-14 on 11,634 ticker-days (2023-11-15 to 2026-11-13), pre-market bars through 08:30 ET, data: alpaca-sip.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: pre-market score vs open-to-close return over SPY | -0.030 | [-0.055, -0.002] |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.00% | [-0.16%, +0.20%] |
| Rank IC: gap vs SPY alone (negative = gaps fade) | -0.013 | |

The 95% interval is entirely below zero: strong pre-market setups have tended to *underperform* SPY after the open, consistent with gaps fading during the session.


## Setup

- **Universe:** ALAB, AMD, AMZN, BE, CEG, DELL, ETN, FSLR, GEV, GOOG, IBM, MRVL, NVDA, SKHY, SPCX, TSLA, TSM, VST; benchmark SPY.
- **Sample:** 752 trading days, 11,634 ticker-days with a full pre-market score.
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
| STRONG PRICE/VOLUME | 405 | +0.09% | -0.19% | +0.38% | -0.10% | 47.4% |
| POSITIVE | 747 | +0.04% | -0.11% | +0.26% | -0.01% | 49.7% |
| WATCH | 1,929 | -0.09% | -0.25% | +0.04% | -0.04% | 48.9% |
| WEAK | 8,553 | +0.05% | -0.03% | +0.14% | -0.02% | 49.7% |

## Baselines

| signal | ic |
|---|---:|
| Pre-market score (this model) | -0.030 |
| Gap vs SPY only | -0.013 |
| Gap / ATR only | -0.012 |
| Pre-market RVOL only | +0.002 |
| Prior close end-of-day score only | -0.028 |
| Shuffled score (null) | -0.005 |

The gap rows answer a classic market-microstructure question directly: a negative IC means
pre-market moves have tended to reverse after the open (gap fade); a positive IC means they
have tended to extend (gap continuation).

## Ablation

| removed | ic | change |
|---|---:|---:|
| gap | -0.027 | +0.002 |
| volume | -0.025 | +0.005 |
| level | -0.033 | -0.003 |
| context | -0.022 | +0.008 |

A negative *change* means removing the component lowers the IC, i.e. it was contributing.

## By ticker

| ticker | n | ic | mean_gap_abs |
|---|---:|---:|---:|
| ALAB | 647 | -0.012 | 2.05% |
| AMD | 752 | +0.020 | 1.52% |
| AMZN | 752 | -0.024 | 0.80% |
| BE | 751 | -0.010 | 2.05% |
| CEG | 679 | -0.014 | 1.09% |
| DELL | 747 | -0.064 | 1.39% |
| ETN | 559 | -0.080 | 1.07% |
| FSLR | 741 | -0.032 | 1.10% |
| GEV | 635 | -0.089 | 1.23% |
| GOOG | 752 | -0.024 | 0.79% |
| IBM | 738 | +0.001 | 0.64% |
| MRVL | 752 | -0.057 | 1.81% |
| NVDA | 752 | -0.070 | 1.17% |
| SKHY | 76 | +0.014 | 2.97% |
| SPCX | 94 | +0.041 | 1.48% |
| TSLA | 752 | -0.034 | 1.26% |
| TSM | 752 | -0.112 | 1.24% |
| VST | 703 | -0.020 | 1.30% |

## Limitations

- A few years of history for a handful of stocks; SPCX and SKHY add only a few months.
- Intraday prices are not dividend-adjusted; on ex-dividend days the measured gap includes the
  dividend. The effect is small for this universe.
- Open-to-close returns ignore the cost of trading at the open, when spreads are widest.
- 18 correlated stocks; several comparisons on the same data. Not investment advice.
