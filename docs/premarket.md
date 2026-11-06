# Pre-market snapshot

**Session:** 2026-11-06 · **Pre-market bars through:** 06:10 ET
(run at 06:29 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **NVDA** | 60.5 | POSITIVE | 189.00 | 181.59 | +4.1% | +3.8% | +0.93 | 4.19 | -19.2% | 100% |
| **AMD** | 57.1 | WATCH | 431.74 | 402.51 | +7.3% | +6.9% | +0.80 | 2.81 | -31.2% | 100% |
| **ALAB** | 54.4 | WATCH | 192.40 | 178.64 | +7.7% | +7.4% | +0.52 | 3.10 | -45.0% | 100% |
| **MRVL** | 53.2 | WATCH | 143.71 | 133.32 | +7.8% | +7.5% | +0.54 | 2.81 | -49.4% | 100% |
| **FSLR** | 52.5 | WATCH | 197.75 | 195.77 | +1.0% | +0.7% | +0.14 | 1.55 | -8.0% | 100% |
| **ETN** | 50.5 | WATCH | 339.00 | 326.52 | +3.8% | +3.5% | +0.59 | 2.33 | -21.9% | 100% |
| **SKHY** | 45.5 | WATCH | 129.00 | 123.38 | +4.6% | +4.2% | +0.52 | 1.82 | -25.6% | 100% |
| **VST** | 44.2 | WEAK | 116.00 | 112.90 | +2.7% | +2.4% | +0.33 | 2.01 | -29.4% | 100% |
| **SPCX** | 44.2 | WEAK | 128.30 | 123.39 | +4.0% | +3.7% | +0.56 | 1.68 | -23.2% | 100% |
| **GEV** | 42.6 | WEAK | 793.00 | 770.82 | +2.9% | +2.6% | +0.36 | 1.79 | -21.4% | 100% |
| **TSLA** | 39.1 | WEAK | 349.00 | 343.44 | +1.6% | +1.3% | +0.27 | 1.30 | -15.7% | 100% |
| **CEG** | 32.9 | WEAK | 242.00 | 239.63 | +1.0% | +0.7% | +0.13 | 1.17 | -19.8% | 100% |
| **AMZN** | 31.0 | WEAK | 257.80 | 260.51 | -1.0% | -1.4% | -0.37 | 1.19 | -5.6% | 100% |
| **IBM** | 29.5 | WEAK | 243.45 | 247.11 | -1.5% | -1.8% | -0.59 | 1.99 | -6.3% | 100% |
| **GOOG** | 24.5 | WEAK | 282.50 | 281.73 | +0.3% | -0.0% | -0.01 | 0.79 | -20.5% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| NVDA | 29.0 | 30.0 | 0.0 | 1.6 |
| AMD | 27.0 | 28.6 | 0.0 | 1.6 |
| ALAB | 22.8 | 30.0 | 0.0 | 1.6 |
| MRVL | 23.1 | 28.5 | 0.0 | 1.6 |
| FSLR | 17.0 | 17.8 | 1.8 | 15.8 |
| ETN | 23.8 | 25.0 | 0.0 | 1.7 |
| SKHY | 22.8 | 20.6 | 0.0 | 2.1 |
| VST | 20.0 | 22.6 | 0.0 | 1.6 |
| SPCX | 23.4 | 19.1 | 0.0 | 1.7 |
| GEV | 20.4 | 20.3 | 0.0 | 2.0 |
| TSLA | 19.1 | 15.2 | 0.0 | 4.8 |
| CEG | 16.9 | 13.8 | 0.0 | 2.2 |
| AMZN | 9.4 | 3.5 | 3.9 | 14.2 |
| IBM | 6.2 | 5.6 | 3.3 | 14.4 |
| GOOG | 14.8 | 6.9 | 0.0 | 2.8 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
