# Dashboard

**Session:** 2026-10-27 · **Source file:** `reports/market_report_20261027.csv` · regenerated automatically after each U.S. close.

> Signals describe how well today's price, volume and trend line up. They are not
> buy/sell recommendations and not evidence of institutional activity. Whether they
> carry any forward-looking information is tested separately in [evaluation.md](evaluation.md).

## Latest signals

| Ticker | Badge | Score | Close | 1d | 5d vs SPY | RVOL20 | RSI14 | vs 20d high | ATR % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **TSLA** | ![TSLA](badges/TSLA.svg) | 87.1 | 407.46 | +4.0% | +9.0% | 1.23 | 65.5 | +2.6% | +3.4% |
| **SPCX** | ![SPCX](badges/SPCX.svg) | 34.4 | 148.58 | +1.1% | +0.5% | 0.93 | 47.8 | -15.8% | +5.2% |
| **ALAB** | ![ALAB](badges/ALAB.svg) | 29.6 | 286.69 | +10.5% | +0.6% | 1.15 | 43.8 | -28.6% | +8.0% |
| **VRT** | ![VRT](badges/VRT.svg) | 25.6 | 208.56 | +4.4% | +2.4% | 1.50 | 39.0 | -19.2% | +5.6% |
| **KLAC** | ![KLAC](badges/KLAC.svg) | 10.9 | 153.66 | +3.0% | -5.1% | 1.00 | 32.7 | -26.4% | +5.0% |

## Score breakdown

Points earned per component. When an input is unavailable (for example no 200-day EMA yet
after an IPO), that part is left out and the score is re-normalised; *Coverage* shows the share
of the 100 points that could be computed. Below 60% the label is
*INSUFFICIENT DATA*.

| Ticker | Trend (/25) | Volume (/25) | Breakout (/20) | Momentum (/15) | Relative Strength (/15) | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| TSLA | 25.0 | 13.6 | 19.1 | 14.3 | 15.0 | 100% |
| SPCX | 8.0 | 8.7 | 0.0 | 7.3 | 7.3 | 91% |
| ALAB | 9.0 | 12.4 | 0.0 | 4.8 | 3.4 | 100% |
| VRT | 0.0 | 18.0 | 0.0 | 3.1 | 4.4 | 100% |
| KLAC | 0.0 | 9.9 | 0.0 | 1.0 | 0.0 | 100% |

## Label scale

| Label | Score |
|---|---|
| STRONG PRICE/VOLUME | 75–100 |
| POSITIVE | 60–74.9 |
| WATCH | 45–59.9 |
| WEAK | below 45 |
