# Pre-market snapshot

**Session:** 2026-11-06 · **Pre-market bars through:** 04:05 ET
(run at 04:23 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **NVDA** | 49.3 | WATCH | 185.00 | 181.59 | +1.9% | +1.6% | +0.40 | 2.57 | -20.9% | 100% |
| **AMD** | 48.1 | WATCH | 426.00 | 402.51 | +5.8% | +5.6% | +0.64 | 1.94 | -32.1% | 100% |
| **MRVL** | 47.3 | WATCH | 139.90 | 133.32 | +4.9% | +4.7% | +0.34 | 2.42 | -50.7% | 100% |
| **FSLR** | 43.6 | WEAK | 196.91 | 195.77 | +0.6% | +0.3% | +0.06 | 0.93 | -8.4% | 100% |
| **ALAB** | 43.4 | WEAK | 188.48 | 178.64 | +5.5% | +5.3% | +0.37 | 1.89 | -46.1% | 100% |
| **ETN** | 42.2 | WEAK | 334.05 | 326.52 | +2.3% | +2.1% | +0.34 | 1.79 | -23.0% | 100% |
| **SKHY** | 41.2 | WEAK | 126.82 | 123.38 | +2.8% | +2.5% | +0.31 | 1.71 | -26.8% | 100% |
| **SPCX** | 36.8 | WEAK | 126.72 | 123.39 | +2.7% | +2.5% | +0.38 | 1.24 | -24.2% | 100% |
| **TSLA** | 35.2 | WEAK | 348.45 | 343.44 | +1.5% | +1.2% | +0.25 | 0.98 | -15.9% | 100% |
| **AMZN** | 28.7 | WEAK | 256.62 | 260.51 | -1.5% | -1.7% | -0.48 | 1.06 | -6.1% | 100% |
| **GOOG** | 19.2 | WEAK | 282.11 | 281.73 | +0.1% | -0.1% | -0.03 | 0.58 | -20.6% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| NVDA | 21.0 | 26.7 | 0.0 | 1.6 |
| AMD | 24.6 | 21.9 | 0.0 | 1.6 |
| MRVL | 20.1 | 25.6 | 0.0 | 1.6 |
| FSLR | 16.0 | 10.3 | 1.5 | 15.8 |
| ALAB | 20.6 | 21.3 | 0.0 | 1.6 |
| ETN | 20.2 | 20.3 | 0.0 | 1.7 |
| SKHY | 19.6 | 19.5 | 0.0 | 2.1 |
| SPCX | 20.6 | 14.5 | 0.0 | 1.7 |
| TSLA | 18.8 | 11.6 | 0.0 | 4.8 |
| AMZN | 7.8 | 3.1 | 3.5 | 14.2 |
| GOOG | 14.6 | 1.9 | 0.0 | 2.8 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
