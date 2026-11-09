# Pre-market snapshot

**Session:** 2026-11-09 · **Pre-market bars through:** 07:25 ET
(run at 07:44 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **CEG** | 55.6 | WATCH | 255.00 | 249.76 | +2.1% | +1.5% | +0.29 | 4.88 | -15.5% | 100% |
| **AMZN** | 53.6 | WATCH | 266.59 | 259.35 | +2.8% | +2.2% | +0.62 | 0.81 | -2.4% | 100% |
| **AMD** | 48.9 | WATCH | 467.60 | 449.03 | +4.1% | +3.5% | +0.43 | 1.67 | -22.9% | 100% |
| **SPCX** | 38.7 | WEAK | 137.43 | 134.19 | +2.4% | +1.8% | +0.29 | 1.18 | -17.7% | 100% |
| **ALAB** | 36.8 | WEAK | 194.00 | 190.70 | +1.7% | +1.1% | +0.09 | 1.40 | -42.3% | 100% |
| **IBM** | 29.4 | WEAK | 247.00 | 244.95 | +0.8% | +0.2% | +0.08 | 0.32 | -5.0% | 100% |
| **FSLR** | 29.2 | WEAK | 200.00 | 201.22 | -0.6% | -1.2% | -0.23 | 0.35 | -6.9% | 100% |
| **VST** | 28.9 | WEAK | 126.00 | 124.76 | +1.0% | +0.4% | +0.06 | 0.78 | -23.3% | 100% |
| **GEV** | 23.4 | WEAK | 785.06 | 774.11 | +1.4% | +0.8% | +0.11 | 0.24 | -21.9% | 100% |
| **GOOG** | 23.3 | WEAK | 288.60 | 283.74 | +1.7% | +1.1% | +0.30 | 0.48 | -18.8% | 100% |
| **MRVL** | 22.6 | WEAK | 141.20 | 141.19 | +0.0% | -0.6% | -0.05 | 0.71 | -49.2% | 100% |
| **TSLA** | 22.4 | WEAK | 361.62 | 358.16 | +1.0% | +0.4% | +0.08 | 0.50 | -12.7% | 100% |
| **ETN** | 21.6 | WEAK | 346.01 | 341.83 | +1.2% | +0.6% | +0.11 | 0.48 | -20.3% | 100% |
| **SKHY** | 14.9 | WEAK | 124.29 | 127.33 | -2.4% | -3.0% | -0.38 | 0.76 | -25.2% | 100% |
| **NVDA** | 12.4 | WEAK | 175.39 | 186.68 | -6.0% | -6.6% | -1.60 | 8.28 | -23.4% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| CEG | 19.3 | 30.0 | 0.0 | 6.2 |
| AMZN | 24.3 | 7.4 | 7.6 | 14.3 |
| AMD | 21.5 | 19.0 | 0.0 | 8.4 |
| SPCX | 19.4 | 13.9 | 0.0 | 5.5 |
| ALAB | 16.3 | 16.2 | 0.0 | 4.2 |
| IBM | 16.2 | 0.0 | 4.6 | 8.7 |
| FSLR | 11.5 | 0.0 | 2.8 | 14.9 |
| VST | 15.9 | 6.7 | 0.0 | 6.3 |
| GEV | 16.7 | 0.0 | 0.0 | 6.7 |
| GOOG | 19.5 | 0.0 | 0.0 | 3.9 |
| MRVL | 14.3 | 5.0 | 0.0 | 3.3 |
| TSLA | 16.2 | 0.0 | 0.0 | 6.2 |
| ETN | 16.6 | 0.0 | 0.0 | 4.9 |
| SKHY | 9.4 | 1.6 | 0.0 | 4.0 |
| NVDA | 0.0 | 7.5 | 0.0 | 4.9 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
