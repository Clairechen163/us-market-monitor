# Pre-market snapshot

**Session:** 2026-11-06 · **Pre-market bars through:** 05:05 ET
(run at 05:25 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **NVDA** | 59.9 | WATCH | 188.81 | 181.59 | +4.0% | +3.6% | +0.89 | 4.06 | -19.3% | 100% |
| **AMD** | 56.9 | WATCH | 432.50 | 402.51 | +7.5% | +7.1% | +0.81 | 2.76 | -31.1% | 100% |
| **ALAB** | 55.4 | WATCH | 194.22 | 178.64 | +8.7% | +8.4% | +0.59 | 3.04 | -44.5% | 100% |
| **MRVL** | 52.3 | WATCH | 143.17 | 133.32 | +7.4% | +7.0% | +0.51 | 2.75 | -49.5% | 100% |
| **FSLR** | 51.6 | WATCH | 196.50 | 195.77 | +0.4% | +0.0% | +0.00 | 1.71 | -8.5% | 100% |
| **ETN** | 50.9 | WATCH | 339.00 | 326.52 | +3.8% | +3.5% | +0.58 | 2.40 | -21.9% | 100% |
| **SKHY** | 47.6 | WATCH | 129.46 | 123.38 | +4.9% | +4.6% | +0.56 | 1.97 | -25.3% | 100% |
| **SPCX** | 42.8 | WEAK | 128.30 | 123.39 | +4.0% | +3.6% | +0.55 | 1.55 | -23.2% | 100% |
| **TSLA** | 40.9 | WEAK | 350.60 | 343.44 | +2.1% | +1.7% | +0.36 | 1.35 | -15.4% | 100% |
| **AMZN** | 32.6 | WEAK | 258.47 | 260.51 | -0.8% | -1.2% | -0.32 | 1.38 | -5.4% | 100% |
| **IBM** | 31.9 | WEAK | 244.00 | 247.11 | -1.3% | -1.6% | -0.53 | 2.70 | -6.1% | 100% |
| **GOOG** | 27.5 | WEAK | 283.30 | 281.73 | +0.6% | +0.2% | +0.05 | 0.88 | -20.3% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| NVDA | 28.4 | 30.0 | 0.0 | 1.6 |
| AMD | 27.2 | 28.2 | 0.0 | 1.6 |
| ALAB | 23.8 | 30.0 | 0.0 | 1.6 |
| MRVL | 22.6 | 28.1 | 0.0 | 1.6 |
| FSLR | 15.0 | 19.5 | 1.3 | 15.8 |
| ETN | 23.7 | 25.5 | 0.0 | 1.7 |
| SKHY | 23.3 | 22.2 | 0.0 | 2.1 |
| SPCX | 23.3 | 17.8 | 0.0 | 1.7 |
| TSLA | 20.4 | 15.7 | 0.0 | 4.8 |
| AMZN | 10.2 | 4.0 | 4.1 | 14.2 |
| IBM | 7.0 | 6.9 | 3.5 | 14.4 |
| GOOG | 15.7 | 9.1 | 0.0 | 2.8 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
