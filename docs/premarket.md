# Pre-market snapshot

**Session:** 2026-11-10 · **Pre-market bars through:** 06:15 ET
(run at 06:35 ET) · regenerated automatically on weekday mornings before the open.

**Data:** Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **NVDA** | 47.2 | WATCH | 179.47 | 178.60 | +0.5% | +0.4% | +0.08 | 2.92 | -21.5% | 100% |
| **AMZN** | 42.3 | WEAK | 268.35 | 267.00 | +0.5% | +0.4% | +0.11 | 0.41 | -2.5% | 100% |
| **IBM** | 36.5 | WEAK | 245.86 | 246.15 | -0.1% | -0.2% | -0.08 | 2.14 | -5.4% | 100% |
| **TSM** | 34.4 | WEAK | 390.60 | 388.68 | +0.5% | +0.4% | +0.09 | 1.18 | -12.3% | 100% |
| **CEG** | 30.7 | WEAK | 273.58 | 276.09 | -0.9% | -1.0% | -0.20 | 1.00 | -8.3% | 100% |
| **AMD** | 26.7 | WEAK | 503.00 | 509.02 | -1.2% | -1.3% | -0.17 | 1.00 | -17.0% | 100% |
| **FSLR** | 23.5 | WEAK | 190.61 | 191.59 | -0.5% | -0.6% | -0.11 | 0.18 | -11.3% | 100% |
| **TSLA** | 22.6 | WEAK | 376.81 | 378.00 | -0.3% | -0.4% | -0.09 | 0.47 | -9.0% | 100% |
| **GOOG** | 21.2 | WEAK | 288.28 | 286.03 | +0.8% | +0.7% | +0.18 | 0.34 | -18.9% | 100% |
| **SPCX** | 19.7 | WEAK | 141.40 | 142.12 | -0.5% | -0.6% | -0.11 | 0.53 | -14.9% | 100% |
| **ETN** | 19.5 | WEAK | 359.80 | 359.32 | +0.1% | +0.0% | +0.00 | 0.03 | -16.5% | 100% |
| **ALAB** | 19.1 | WEAK | 215.45 | 217.04 | -0.7% | -0.8% | -0.07 | 0.51 | -34.1% | 100% |
| **GEV** | 18.7 | WEAK | 821.60 | 829.08 | -0.9% | -1.0% | -0.15 | 0.78 | -18.3% | 100% |
| **BE** | 18.4 | WEAK | 192.44 | 193.93 | -0.8% | -0.9% | -0.08 | 0.63 | -27.1% | 100% |
| **MRVL** | 18.1 | WEAK | 152.50 | 154.62 | -1.4% | -1.5% | -0.13 | 0.78 | -43.3% | 100% |
| **VST** | 17.9 | WEAK | 133.00 | 133.88 | -0.7% | -0.8% | -0.12 | 0.34 | -18.7% | 100% |
| **DELL** | 17.7 | WEAK | 344.65 | 346.20 | -0.4% | -0.6% | -0.06 | 0.73 | -40.5% | 100% |
| **SKHY** | 16.0 | WEAK | 132.50 | 134.41 | -1.4% | -1.5% | -0.20 | 0.63 | -20.2% | 100% |

## Score breakdown

| Ticker | Gap (/30) | Volume (/30) | Level (/15) | Context (/25) |
|---|---:|---:|---:|---:|
| NVDA | 16.2 | 29.4 | 0.0 | 1.6 |
| AMZN | 16.6 | 0.0 | 7.5 | 18.2 |
| IBM | 13.8 | 5.9 | 4.1 | 12.7 |
| TSM | 16.3 | 13.9 | 0.0 | 4.2 |
| CEG | 12.0 | 3.0 | 1.5 | 14.2 |
| AMD | 12.4 | 3.0 | 0.0 | 11.3 |
| FSLR | 13.3 | 0.0 | 0.0 | 10.2 |
| TSLA | 13.6 | 0.0 | 0.9 | 8.2 |
| GOOG | 17.7 | 0.0 | 0.0 | 3.5 |
| SPCX | 13.4 | 0.2 | 0.0 | 6.1 |
| ETN | 15.0 | 0.0 | 0.0 | 4.4 |
| ALAB | 13.9 | 0.0 | 0.0 | 5.2 |
| GEV | 12.8 | 1.7 | 0.0 | 4.2 |
| BE | 13.8 | 0.8 | 0.0 | 3.8 |
| MRVL | 13.1 | 1.7 | 0.0 | 3.4 |
| VST | 13.2 | 0.0 | 0.0 | 4.7 |
| DELL | 14.1 | 1.4 | 0.0 | 2.2 |
| SKHY | 11.9 | 0.8 | 0.0 | 3.2 |

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous 10 sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
