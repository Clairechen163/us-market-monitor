# US Market Monitor

**A transparent price/volume signal for U.S. stocks, and a statistical test of whether it actually predicts anything.**

[![Daily Market Monitor](https://github.com/Clairechen163/us-market-monitor/actions/workflows/daily-market-monitor.yml/badge.svg)](https://github.com/Clairechen163/us-market-monitor/actions/workflows/daily-market-monitor.yml)
[![Tests](https://github.com/Clairechen163/us-market-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Clairechen163/us-market-monitor/actions/workflows/tests.yml)

| KLAC | ALAB | SPCX | TSLA | VRT |
|---|---|---|---|---|
| ![KLAC](docs/badges/KLAC.svg) | ![ALAB](docs/badges/ALAB.svg) | ![SPCX](docs/badges/SPCX.svg) | ![TSLA](docs/badges/TSLA.svg) | ![VRT](docs/badges/VRT.svg) |

**[Today's dashboard →](docs/dashboard.md)** · **[Full evaluation →](docs/evaluation.md)**

---

## The question

Market commentary often says a move is "confirmed by volume" or "breaking out on strong
participation". This project turns that idea into an explicit, reproducible score and then
asks the question that matters to a data scientist:

> **When price, volume, trend and breakout behaviour line up at today's close, do those stocks
> outperform the S&P 500 over the following week?**

The project has two halves:

1. **Monitor (descriptive).** Every weekday after the U.S. close, a GitHub Action downloads
   prices, computes indicators, scores each stock from 0 to 100 and publishes badges and a
   dashboard. Any U.S.-listed stock or ETF works; edit `TICKERS` in `monitor/config.py`
   (default: KLAC, ALAB, SPCX, TSLA, VRT).
2. **Evaluation (inferential).** Every week, the same scoring rules are replayed over five years
   of history and tested against forward returns with time-series-aware statistics,
   baselines, ablations and an out-of-sample model.

## Results

<!-- EVAL:START -->
*Last evaluated 2026-10-17 on 4,375 ticker-days (2021-11-15 to 2026-10-09), 5-day horizon, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: score vs forward return over SPY | +0.019 | [-0.044, +0.079] |
| Rank IC, non-overlapping windows only | -0.022 | |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.34% | [-0.54%, +1.41%] |
| Out-of-sample AUC: hand weights vs learned weights | 0.500 vs 0.473 | |

The 95% interval for the IC includes zero, so the data do not support a claim that the score predicts forward relative returns. That is a legitimate finding: the score is useful as a description of today's move, not as a forecast.

Full write-up: [docs/evaluation.md](docs/evaluation.md)
<!-- EVAL:END -->

## Methods

### Score (0–100)

| Component | Weight | Input | Mapping |
|---|---:|---|---|
| Trend | 25 | Close vs EMA20 and EMA200; EMA20 vs EMA50 | three binary checks, weighted 8 / 9 / 8 |
| Volume | 25 | RVOL20 = today's volume / mean of previous 20 sessions | 0.5→0, 1.0→40%, 1.5→72%, ≥2.0→100%; cut by 75% on down days |
| Breakout | 20 | Close vs highest high of previous 20 sessions | −10%→0, at the high→70%, +3%→100% |
| Momentum | 15 | RSI14 (Wilder) | peaks at 55–70, fades when overbought |
| Relative strength | 15 | 5- and 20-day return in excess of SPY | −5%→0, 0→50%, +5%→100% (20d range doubled) |

Labels: **STRONG PRICE/VOLUME** ≥ 75 · **POSITIVE** 60–74.9 · **WATCH** 45–59.9 · **WEAK** < 45.

Design decisions worth noting:

- **Piecewise-linear, not hard thresholds.** A tiny change in an input cannot swing the score
  by many points.
- **High volume on a down day is not confirmation.** It is treated as distribution and mostly
  discounted.
- **Missing data is handled explicitly.** SPCX (SpaceX) only listed in June 2026, so it has no
  200-day EMA yet. Instead of scoring the missing input as zero, which would bias new listings
  downward, the score is re-normalised over the inputs that exist and a `coverage` field reports
  how much of the model could be computed. Below 60% coverage the label is *INSUFFICIENT DATA*.
- **No look-ahead.** Every value at day *t* uses data through the close of *t* only. A unit test
  multiplies all future prices by 3 and checks that no past score changes.

### Evaluation

| Step | Why |
|---|---|
| Target = 5-day forward return **minus SPY** | Removes the market's direction, so the test is about stock selection, not whether the market went up |
| Spearman rank IC | Robust to the fat tails of daily returns |
| Moving-block bootstrap (20-day blocks of dates) | Forward windows overlap and stocks are correlated; i.i.d. resampling would give falsely narrow intervals |
| Non-overlapping subsample, IC by year, rolling IC | Checks the result is not driven by one period |
| Baselines: momentum only, RVOL only, shuffled score | A composite should beat its simplest ingredients and a null |
| Ablation: drop each component, re-score | Shows which inputs carry information |
| Walk-forward logistic regression with a 5-day purge gap | Tests whether learned weights beat hand-chosen ones on unseen dates without label leakage |

## Repository layout

```
monitor/
  config.py        universe, weights, label thresholds (single source of truth)
  indicators.py    EMA, Wilder RSI/ATR, RVOL, prior high, benchmark-relative returns
  scoring.py       component maps, coverage re-normalisation, labels, ablation hook
  data.py          Yahoo Finance loader with CSV cache; synthetic generator for tests
  pipeline.py      OHLCV -> indicators -> scores panel
  evaluation.py    forward returns, IC, block bootstrap, baselines, walk-forward model
  report.py        daily text and CSV report
market_monitor.py        daily CLI
scripts/
  update_dashboard.py    badges + docs/dashboard.md from the latest CSV
  evaluate_signal.py     docs/evaluation.md, figures, README results block
tests/                   22 tests: indicator math, scoring rules, no-look-ahead, evaluation, CLI
.github/workflows/       daily monitor, weekly evaluation, tests on Python 3.10 and 3.12
```

## Run it

```bash
git clone https://github.com/Clairechen163/us-market-monitor.git
cd us-market-monitor
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python market_monitor.py                 # today's report -> reports/
python scripts/update_dashboard.py       # badges + dashboard -> docs/
python scripts/evaluate_signal.py        # evaluation -> docs/evaluation.md
pytest -q                                # test suite (runs offline)
```

Useful options: `--tickers NVDA AMD AVGO` to change the universe, `--horizon 10` for the
evaluation, and `--source synthetic` to try everything without a network connection
(synthetic results are labelled and never published to the dashboard or README).

## Limitations

- The default universe is five stocks, several of them tied to the AI build-out, so results may
  not generalise. Adding names from other sectors (banks, healthcare, energy, consumer) is the
  most direct way to test that.
- Yahoo Finance data via `yfinance` is free but unofficial; a licensed feed would be needed for
  production use.
- No transaction costs, slippage or survivorship-bias control.
- The score is descriptive. A positive IC would be a statistical association, not a trading
  strategy, and public OHLCV data cannot reveal *who* is buying.

**Not investment advice.**

## License

MIT
