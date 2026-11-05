# Pre-market snapshot

**Session:** 2026-11-05 · **Pre-market bars through:** 07:45 ET
(run at 08:01 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **FSLR** | 83.1 | STRONG PRICE/VOLUME | 202.92 | 194.51 | +4.3% | +4.3% | +0.91 | 3.82 | -5.6% | 100% |
| **AMZN** | 66.5 | POSITIVE | 270.16 | 266.14 | +1.5% | +1.5% | +0.46 | 1.21 | -0.5% | 100% |
| **GOOG** | 32.1 | WEAK | 290.72 | 287.41 | +1.2% | +1.1% | +0.31 | 0.85 | -18.2% | 100% |
| **AMD** | 18.8 | WEAK | 467.97 | 488.75 | -4.3% | -4.3% | -0.67 | 1.59 | -27.3% | 100% |
| **TSLA** | 18.7 | WEAK | 376.94 | 385.31 | -2.2% | -2.2% | -0.60 | 0.76 | -9.0% | 100% |
| **ETN** | 16.4 | WEAK | 345.23 | 352.82 | -2.2% | -2.2% | -0.41 | 1.93 | -21.4% | 100% |
| **NVDA** | 14.2 | WEAK | 197.15 | 200.29 | -1.6% | -1.6% | -0.50 | 1.80 | -16.8% | 100% |
| **MRVL** | 13.7 | WEAK | 152.60 | 159.91 | -4.6% | -4.6% | -0.41 | 1.18 | -46.2% | 100% |
| **ALAB** | 13.4 | WEAK | 212.66 | 223.27 | -4.8% | -4.8% | -0.45 | 1.17 | -44.5% | 100% |
| **SPCX** | 11.2 | WEAK | 132.55 | 135.83 | -2.4% | -2.4% | -0.45 | 0.64 | -20.9% | 100% |
| **SKHY** | 5.8 | WEAK | 134.35 | 143.08 | -6.1% | -6.1% | -0.94 | 1.07 | -24.2% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| FSLR | 28.7 | 30.0 | 4.0 | 20.4 |
| AMZN | 21.9 | 14.2 | 9.9 | 20.6 |
| GOOG | 19.7 | 8.4 | 0.0 | 4.0 |
| AMD | 4.9 | 4.5 | 0.0 | 9.3 |
| TSLA | 5.9 | 1.6 | 0.9 | 10.2 |
| ETN | 8.8 | 5.4 | 0.0 | 2.1 |
| NVDA | 7.6 | 5.1 | 0.0 | 1.5 |
| MRVL | 8.8 | 3.5 | 0.0 | 1.4 |
| ALAB | 8.3 | 3.4 | 0.0 | 1.7 |
| SPCX | 8.3 | 0.9 | 0.0 | 2.0 |
| SKHY | 0.9 | 3.2 | 0.0 | 1.7 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
