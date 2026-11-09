# Pre-market snapshot

**Session:** 2026-11-09 · **Pre-market bars through:** 04:55 ET
(run at 05:11 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **CEG** | 43.1 | WEAK | 252.00 | 249.76 | +0.9% | +0.5% | +0.09 | 1.81 | -16.5% | 100% |
| **AMD** | 41.1 | WEAK | 459.00 | 449.03 | +2.2% | +1.8% | +0.22 | 1.23 | -24.3% | 100% |
| **SPCX** | 37.3 | WEAK | 136.50 | 134.19 | +1.7% | +1.3% | +0.21 | 1.16 | -18.3% | 100% |
| **ALAB** | 37.2 | WEAK | 195.00 | 190.70 | +2.3% | +1.8% | +0.14 | 1.37 | -42.0% | 100% |
| **AMZN** | 35.2 | WEAK | 260.91 | 259.35 | +0.6% | +0.2% | +0.05 | 0.36 | -4.5% | 100% |
| **IBM** | 30.3 | WEAK | 247.00 | 244.95 | +0.8% | +0.4% | +0.13 | 0.46 | -5.0% | 100% |
| **VST** | 29.4 | WEAK | 124.82 | 124.76 | +0.0% | -0.4% | -0.06 | 0.87 | -24.0% | 100% |
| **ETN** | 28.8 | WEAK | 343.00 | 341.83 | +0.3% | -0.1% | -0.01 | 0.88 | -21.0% | 100% |
| **FSLR** | 26.7 | WEAK | 198.38 | 201.22 | -1.4% | -1.8% | -0.35 | 0.28 | -7.7% | 100% |
| **GEV** | 23.4 | WEAK | 778.00 | 774.11 | +0.5% | +0.1% | +0.01 | 0.56 | -22.6% | 100% |
| **TSLA** | 21.1 | WEAK | 358.86 | 358.16 | +0.2% | -0.2% | -0.05 | 0.52 | -13.4% | 100% |
| **GOOG** | 20.7 | WEAK | 286.28 | 283.74 | +0.9% | +0.5% | +0.13 | 0.33 | -19.4% | 100% |
| **MRVL** | 19.0 | WEAK | 139.80 | 141.19 | -1.0% | -1.4% | -0.11 | 0.89 | -49.7% | 100% |
| **SKHY** | 15.5 | WEAK | 124.60 | 127.33 | -2.1% | -2.6% | -0.32 | 0.73 | -25.0% | 100% |
| **NVDA** | 12.4 | WEAK | 178.10 | 186.68 | -4.6% | -5.0% | -1.21 | 5.71 | -22.2% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| CEG | 16.4 | 20.5 | 0.0 | 6.2 |
| AMD | 18.3 | 14.4 | 0.0 | 8.4 |
| SPCX | 18.1 | 13.7 | 0.0 | 5.5 |
| ALAB | 17.1 | 15.9 | 0.0 | 4.2 |
| AMZN | 15.7 | 0.0 | 5.1 | 14.3 |
| IBM | 17.0 | 0.0 | 4.6 | 8.7 |
| VST | 14.2 | 8.9 | 0.0 | 6.3 |
| ETN | 14.8 | 9.1 | 0.0 | 4.9 |
| FSLR | 9.7 | 0.0 | 2.1 | 14.9 |
| GEV | 15.2 | 1.5 | 0.0 | 6.7 |
| TSLA | 14.3 | 0.6 | 0.0 | 6.2 |
| GOOG | 16.9 | 0.0 | 0.0 | 3.9 |
| MRVL | 13.3 | 2.3 | 0.0 | 3.3 |
| SKHY | 10.2 | 1.4 | 0.0 | 4.0 |
| NVDA | 0.0 | 7.5 | 0.0 | 4.9 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
