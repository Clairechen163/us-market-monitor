# US Market Monitor

**A transparent price/volume signal for U.S. stocks, and a statistical test of whether it actually predicts anything.**

[![Daily Market Monitor](https://github.com/Clairechen163/us-market-monitor/actions/workflows/daily-market-monitor.yml/badge.svg)](https://github.com/Clairechen163/us-market-monitor/actions/workflows/daily-market-monitor.yml)
[![Pre-market Monitor](https://github.com/Clairechen163/us-market-monitor/actions/workflows/premarket-monitor.yml/badge.svg)](https://github.com/Clairechen163/us-market-monitor/actions/workflows/premarket-monitor.yml)
[![Tests](https://github.com/Clairechen163/us-market-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/Clairechen163/us-market-monitor/actions/workflows/tests.yml)

| ALAB | AMD | NVDA | MRVL | GOOG |
|---|---|---|---|---|
| ![ALAB](docs/badges/ALAB.svg) | ![AMD](docs/badges/AMD.svg) | ![NVDA](docs/badges/NVDA.svg) | ![MRVL](docs/badges/MRVL.svg) | ![GOOG](docs/badges/GOOG.svg) |

| AMZN | IBM | FSLR | SKHY | ETN |
|---|---|---|---|---|
| ![AMZN](docs/badges/AMZN.svg) | ![IBM](docs/badges/IBM.svg) | ![FSLR](docs/badges/FSLR.svg) | ![SKHY](docs/badges/SKHY.svg) | ![ETN](docs/badges/ETN.svg) |

| GEV | CEG | VST | TSLA | SPCX |
|---|---|---|---|---|
| ![GEV](docs/badges/GEV.svg) | ![CEG](docs/badges/CEG.svg) | ![VST](docs/badges/VST.svg) | ![TSLA](docs/badges/TSLA.svg) | ![SPCX](docs/badges/SPCX.svg) |

**[Live dashboard →](#live-dashboard)** · **[End-of-day dashboard →](docs/dashboard.md)** · **[Pre-market snapshot →](docs/premarket.md)** · **[End-of-day evaluation →](docs/evaluation.md)** · **[Pre-market evaluation →](docs/premarket_evaluation.md)**

## Key findings

<!-- FINDINGS-EOD:START -->
- **End-of-day signal: no evidence of predictive power.** The rank IC between the score and the next 5 days' return over SPY is +0.001 (95% CI -0.042 to +0.039) across 14,875 stock-days; a randomly shuffled score gets +0.000.
<!-- FINDINGS-EOD:END -->
<!-- FINDINGS-PM:START -->
- **Pre-market signal: no evidence of predictive power.** The rank IC between the 08:30 ET pre-market score and the same day's open-to-close return over SPY is -0.019 (95% CI -0.052 to +0.010) across 7,999 stock-days; a randomly shuffled score gets +0.013. On their own, the pre-market gap has an IC of -0.006 (negative would mean gaps fade).
<!-- FINDINGS-PM:END -->
- **How it was tested:** a common trading belief, that moves confirmed by volume keep going, is
  turned into a transparent score and tested on end-of-day and pre-market data with
  time-series-aware methods: a block bootstrap, look-ahead tests, baselines, ablations,
  walk-forward validation and a shuffled control. The figures above refresh automatically
  after each weekly evaluation; details are under [Results](#results).

---

## The question

Market commentary often says a move is "confirmed by volume" or "breaking out on strong
participation". This project turns that idea into an explicit, reproducible score and then
asks the question that matters to a data scientist:

> **When price, volume, trend and breakout behaviour line up at today's close, do those stocks
> outperform the S&P 500 over the following week?**

and the same question earlier in the day:

> **When a stock is gapping up on heavy pre-market volume, does it keep outperforming the S&P 500
> after the open, or does the gap fade?**

The project has two halves, each run on end-of-day and on pre-market data:

1. **Monitor (descriptive).** Every weekday after the U.S. close, a GitHub Action downloads
   prices, computes indicators, scores each stock from 0 to 100 and publishes badges and a
   dashboard. Any U.S.-listed stock or ETF works; edit `TICKERS` in `monitor/config.py`
   (default: ALAB, AMD, NVDA, MRVL, GOOG, AMZN, IBM, FSLR, SKHY, ETN, GEV, CEG, VST, TSLA, SPCX).
   A second action runs at about 08:55 ET, before the open, and scores the pre-market session
   (from 04:00 ET) using bars through 08:30 ET.
2. **Evaluation (inferential).** Every week, the same scoring rules are replayed over history
   (five years of daily bars; about three years of 30-minute pre-market bars) and tested against
   what happened next, with time-series-aware statistics, baselines and ablations.

## Results

### End-of-day score → next 5 days

<!-- EVAL:START -->
*Last evaluated 2026-11-06 on 14,875 ticker-days (2021-12-07 to 2026-10-30), 5-day horizon, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: score vs forward return over SPY | +0.001 | [-0.042, +0.039] |
| Rank IC, non-overlapping windows only | -0.007 | |
| Mean return gap: POSITIVE-or-better minus WEAK | +0.37% | [-0.25%, +0.85%] |
| Out-of-sample AUC: hand weights vs learned weights | 0.497 vs 0.505 | |

The 95% interval for the IC includes zero, so the data do not support a claim that the score predicts forward relative returns. That is a legitimate finding: the score is useful as a description of today's move, not as a forecast.

Full write-up: [docs/evaluation.md](docs/evaluation.md)
<!-- EVAL:END -->

### Pre-market score → same-day open-to-close

<!-- PREMARKET-EVAL:START -->
*Last evaluated 2026-11-06 on 7,999 ticker-days (2023-12-27 to 2026-11-06), pre-market bars through 08:30 ET, data: yahoo.*

| Metric | Estimate | 95% CI |
|---|---:|---:|
| Rank IC: pre-market score vs open-to-close return over SPY | -0.019 | [-0.052, +0.010] |
| Mean return gap: POSITIVE-or-better minus WEAK | -0.05% | [-0.23%, +0.12%] |
| Rank IC: gap vs SPY alone (negative = gaps fade) | -0.006 | |

The 95% interval includes zero, so the data do not show that the pre-market score predicts the regular session. It describes the pre-market well; it is not a forecast.

Full write-up: [docs/premarket_evaluation.md](docs/premarket_evaluation.md)
<!-- PREMARKET-EVAL:END -->

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
  200-day EMA yet. SK hynix (SKHY) is in the same position since its July 2026 Nasdaq ADR listing.
  Instead of scoring the missing input as zero, which would bias new listings
  downward, the score is re-normalised over the inputs that exist and a `coverage` field reports
  how much of the model could be computed. Below 60% coverage the label is *INSUFFICIENT DATA*.
- **No look-ahead.** Every value at day *t* uses data through the close of *t* only. A unit test
  multiplies all future prices by 3 and checks that no past score changes.

### Pre-market score (0–100)

Computed from pre-market bars that closed by **08:30 ET**, with daily context taken from the
previous completed session. The live snapshot and the historical evaluation use the same 08:30
cut-off, so the evaluation tests exactly what the daily page shows.

| Component | Weight | Input | Mapping |
|---|---:|---|---|
| Gap | 30 | (pre-market price / prior close − 1) minus SPY's gap, divided by ATR14 % | −1 ATR→0, 0→50%, +1 ATR→100% |
| Volume | 30 | Pre-market volume so far / average over the **same clock window** on the previous 10 sessions | 0.5→0, 1.0→40%, 2.0→75%, ≥3.0→100%; cut by 75% when gapping down |
| Level | 15 | Pre-market price vs highest high of the prior 20 sessions | −10%→0, at the high→70%, +3%→100% |
| Context | 25 | Prior close's end-of-day score | score / 100 |

- **Gap in ATR units.** A 3% gap is routine for TSLA and unusual for ETN; dividing by each stock's
  normal daily range makes gaps comparable.
- **Same-time volume baseline.** Pre-market volume builds through the morning, so 08:30 volume is
  compared with 08:30 volume on earlier days, never with a full session.
- **Pre-market data from Alpaca, not Yahoo.** Yahoo reports zero volume for every extended-hours
  bar, so pre-market volume cannot be measured from it. Pre-market bars therefore come from
  Alpaca's SIP feed, which consolidates trades from every U.S. exchange, pre-market included. The
  free plan withholds the latest 15 minutes, which is why the snapshot is scored at 08:30 and the
  job runs at 08:55. Without Alpaca keys the monitor falls back to Yahoo prices, leaves the volume
  component out and re-normalises the score (coverage 70%); each report states which source it used.

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
| Pre-market: target = open-to-close return **minus SPY**, same day | Starts at 09:30, after every input is known; one-day windows do not overlap |
| Pre-market: gap-only baseline | Answers gap fade vs gap continuation directly |

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
  intraday.py      extended-hours bars in New York time; synthetic sessions for tests
  alpaca.py        Alpaca Market Data v2 client: bars, real-time latest trades, paging, retries
  live.py          live scores for the web dashboard (pre-market, intraday, latest close)
  premarket.py     session splitting, pre-market features and score
  premarket_eval.py  pre-market score vs same-day open-to-close return
market_monitor.py        end-of-day CLI
premarket_monitor.py     pre-market CLI -> reports/premarket/, docs/premarket.md
app/streamlit_app.py     live web dashboard (Streamlit)
scripts/
  update_dashboard.py    badges + docs/dashboard.md from the latest CSV
  evaluate_signal.py     docs/evaluation.md, figures, README results block
  evaluate_premarket.py  docs/premarket_evaluation.md, figure, README results block
tests/                   81 tests: indicator math, scoring rules, no-look-ahead (daily and
                         pre-market), session boundaries, daylight saving, Alpaca client
                         (mocked HTTP), live scores, dashboard in every market phase,
                         evaluation, CLI
.github/workflows/       end-of-day monitor, pre-market monitor, weekly evaluation, tests
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
python premarket_monitor.py              # pre-market snapshot -> reports/premarket/, docs/premarket.md
python scripts/evaluate_premarket.py     # pre-market evaluation -> docs/premarket_evaluation.md
pytest -q                                # test suite (runs offline)
```

### Pre-market data (Alpaca, free)

1. Create a free account at [alpaca.markets](https://alpaca.markets); a paper-trading account is
   enough, and no money is involved.
2. In the Alpaca dashboard, generate an API key and copy the **Key ID** and **Secret Key**.
3. In this GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**,
   add `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY`.

Locally, set the same two environment variables. Keys are read only from the environment and are
never written to reports or logs.

### Live dashboard

A Streamlit app recomputes the scores from live data every time it is opened, and refreshes
every minute:

- **04:00–09:30 ET:** live pre-market score.
- **09:30–16:00 ET:** the end-of-day score as if the session ended now, with volume since the
  open compared with the same window on the previous 20 sessions.
- **After the close:** the end-of-day score for the latest session.

Prices are real-time trades from the IEX exchange (Alpaca's free plan); volume covers every U.S.
exchange and runs about 15 minutes behind. Each view states the time of its latest price and
volume.

Run it locally with `streamlit run app/streamlit_app.py` (with the two Alpaca variables set),
or deploy it free on [Streamlit Community Cloud](https://share.streamlit.io): **Create app →**
this repo, branch `main`, main file `app/streamlit_app.py` → **Advanced settings → Secrets**:

```toml
ALPACA_API_KEY_ID = "your key id"
ALPACA_API_SECRET_KEY = "your secret key"
```

Useful options: `--tickers NVDA AMD AVGO` to change the universe, `--horizon 10` for the
evaluation, and `--source synthetic` to try everything without a network connection
(synthetic results are labelled and never published to the dashboard or README).

## Limitations

- The default universe is fifteen stocks, most of them exposed to AI infrastructure (chips, memory,
  cloud, enterprise software, data-centre power, power generation, solar), so they tend to move together and results may not generalise.
  Adding names from other sectors (banks, healthcare, consumer) is the most direct way to test that.
- SPCX and SKHY only listed in mid-2026, so they contribute few observations to the evaluation
  and have no 200-day trend input yet (see *coverage* above).
- Pre-market history covers about three years (Alpaca's free plan), and pre-market trading is
  thin, so a few large trades can move a stock's pre-market RVOL.
- Daily prices come from Yahoo Finance via `yfinance`, which is free but unofficial; a licensed
  feed would be needed for production use.
- No transaction costs, slippage or survivorship-bias control.
- The score is descriptive. A positive IC would be a statistical association, not a trading
  strategy, and public OHLCV data cannot reveal *who* is buying.

**Not investment advice.**

## License

MIT
