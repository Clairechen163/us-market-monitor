# Pre-market snapshot

**Session:** 2026-11-06 · **Pre-market bars through:** 08:30 ET
(run at 11:04 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **NVDA** | 61.6 | POSITIVE | 189.55 | 181.59 | +4.4% | +4.1% | +1.01 | 3.37 | -19.0% | 100% |
| **AMD** | 55.5 | WATCH | 438.00 | 402.51 | +8.8% | +8.5% | +0.98 | 2.24 | -30.2% | 100% |
| **ALAB** | 53.5 | WATCH | 195.20 | 178.64 | +9.3% | +9.0% | +0.63 | 2.67 | -44.2% | 100% |
| **VST** | 53.1 | WATCH | 119.90 | 112.90 | +6.2% | +5.9% | +0.81 | 2.25 | -27.0% | 100% |
| **MRVL** | 49.9 | WATCH | 146.50 | 133.32 | +9.9% | +9.6% | +0.69 | 2.06 | -48.4% | 100% |
| **AMZN** | 49.9 | WATCH | 261.80 | 260.51 | +0.5% | +0.2% | +0.05 | 1.24 | -4.2% | 100% |
| **FSLR** | 46.3 | WATCH | 196.50 | 195.77 | +0.4% | +0.1% | +0.01 | 1.19 | -8.5% | 100% |
| **ETN** | 46.1 | WATCH | 344.00 | 326.52 | +5.4% | +5.0% | +0.84 | 1.45 | -20.7% | 100% |
| **SPCX** | 45.5 | WATCH | 129.42 | 123.39 | +4.9% | +4.6% | +0.70 | 1.60 | -22.5% | 100% |
| **SKHY** | 43.9 | WEAK | 129.88 | 123.38 | +5.3% | +5.0% | +0.60 | 1.55 | -25.1% | 100% |
| **TSLA** | 38.1 | WEAK | 350.20 | 343.44 | +2.0% | +1.7% | +0.35 | 1.10 | -15.5% | 100% |
| **GEV** | 37.0 | WEAK | 798.61 | 770.82 | +3.6% | +3.3% | +0.46 | 1.11 | -20.9% | 100% |
| **CEG** | 36.8 | WEAK | 246.10 | 239.63 | +2.7% | +2.4% | +0.44 | 1.09 | -18.4% | 100% |
| **GOOG** | 33.2 | WEAK | 282.40 | 281.73 | +0.2% | -0.1% | -0.02 | 1.36 | -20.5% | 100% |
| **IBM** | 28.1 | WEAK | 244.50 | 247.11 | -1.1% | -1.4% | -0.45 | 0.79 | -5.9% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| NVDA | 30.0 | 30.0 | 0.0 | 1.6 |
| AMD | 29.7 | 24.3 | 0.0 | 1.6 |
| ALAB | 24.4 | 27.5 | 0.0 | 1.6 |
| VST | 27.1 | 24.4 | 0.0 | 1.6 |
| MRVL | 25.4 | 23.0 | 0.0 | 1.6 |
| AMZN | 15.7 | 14.5 | 5.5 | 14.2 |
| FSLR | 15.2 | 14.0 | 1.3 | 15.8 |
| ETN | 27.7 | 16.7 | 0.0 | 1.7 |
| SPCX | 25.5 | 18.2 | 0.0 | 1.7 |
| SKHY | 24.0 | 17.8 | 0.0 | 2.1 |
| TSLA | 20.2 | 13.0 | 0.0 | 4.8 |
| GEV | 21.9 | 13.1 | 0.0 | 2.0 |
| CEG | 21.6 | 12.9 | 0.0 | 2.2 |
| GOOG | 14.7 | 15.8 | 0.0 | 2.8 |
| IBM | 8.2 | 1.7 | 3.7 | 14.4 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
