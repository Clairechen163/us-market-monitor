"""Central configuration: universe, benchmark, score weights and label thresholds.

Everything that defines the model lives here so that the scoring rules are
auditable in one place and the evaluation can refer to exactly the same
definitions the daily monitor uses.
"""

from __future__ import annotations

TICKERS: list[str] = [
    "ALAB",  # Astera Labs: AI connectivity chips
    "AMD",   # Advanced Micro Devices: CPUs / GPUs
    "NVDA",  # NVIDIA: GPUs
    "MRVL",  # Marvell: custom silicon, networking
    "TSM",   # TSMC (NYSE ADR): contract chip manufacturing
    "GOOG",  # Alphabet: cloud, search, TPUs
    "AMZN",  # Amazon: AWS cloud, e-commerce, Trainium chips
    "IBM",   # IBM: hybrid cloud, consulting, enterprise AI, quantum
    "DELL",  # Dell Technologies: AI servers, storage, PCs
    "FSLR",  # First Solar: solar modules
    "SKHY",  # SK hynix ADR: memory / HBM (Nasdaq from Jul 2026)
    "ETN",   # Eaton: power management, data-centre electrical
    "GEV",   # GE Vernova: gas turbines, grid equipment, wind (NYSE from Apr 2024)
    "CEG",   # Constellation Energy: largest U.S. nuclear fleet (Nasdaq from Feb 2022)
    "VST",   # Vistra: power generation and retail electricity
    "BE",    # Bloom Energy: on-site fuel-cell power
    "TSLA",  # Tesla: EVs, energy storage
    "SPCX",  # SpaceX: launch, Starlink, xAI (Nasdaq from Jun 2026)
]

# First U.S. trading day for recent listings. Bars before these dates are
# dropped: a reused symbol can carry an unrelated security's history (SPCX was
# previously an ETF ticker), which would silently corrupt indicators.
LISTING_DATES: dict[str, str] = {
    "SPCX": "2026-06-12",
    "SKHY": "2026-07-10",  # traded as SKHYV (when-issued) until 2026-07-13
    "GEV": "2024-04-02",   # spun off from GE; traded as "GEV WI" from 2024-03-27
    "CEG": "2022-02-02",   # spun off from Exelon; CEG was Constellation Energy Group's symbol until 2012
}

# Relative strength is measured against this ETF (S&P 500).
BENCHMARK: str = "SPY"

# Years of daily history pulled for indicators and for the evaluation.
HISTORY_PERIOD: str = "5y"

# Component weights (sum to 100).
WEIGHTS: dict[str, float] = {
    "trend": 25.0,
    "volume": 25.0,
    "breakout": 20.0,
    "momentum": 15.0,
    "relative_strength": 15.0,
}

# Label thresholds, evaluated top-down.
LABELS: list[tuple[float, str]] = [
    (75.0, "STRONG PRICE/VOLUME"),
    (60.0, "POSITIVE"),
    (45.0, "WATCH"),
    (0.0, "WEAK"),
]

# If less than this share of the 100 points can be computed (e.g. a recent
# IPO with no EMA200 yet), the row is labelled INSUFFICIENT DATA instead.
MIN_COVERAGE: float = 0.60
INSUFFICIENT_LABEL: str = "INSUFFICIENT DATA"

# Forward horizon (trading days) used by the evaluation.
FORWARD_HORIZON: int = 5

assert abs(sum(WEIGHTS.values()) - 100.0) < 1e-9, "weights must sum to 100"


# --------------------------------------------------------------------------
# Pre-market monitor (04:00-09:30 ET)
# --------------------------------------------------------------------------
PREMARKET_WEIGHTS: dict[str, float] = {
    "gap": 30.0,      # pre-market price vs prior close, relative to SPY, in ATR units
    "volume": 30.0,   # pre-market volume vs the same clock time on recent days
    "level": 15.0,    # pre-market price vs the prior 20-session high
    "context": 25.0,  # prior close's end-of-day score (trend, momentum, ...)
}

# Fixed snapshot time for the pre-market score (ET). Live runs and the
# historical evaluation both use bars that closed by this time, so the
# evaluation measures exactly what the daily snapshot shows.
PREMARKET_SNAPSHOT_TIME: str = "08:30"

# Years of 30-minute history requested from Alpaca for the evaluation.
PREMARKET_EVAL_YEARS: int = 3

# Sessions used to build the "normal" pre-market volume baseline.
PREMARKET_RVOL_WINDOW: int = 10

# Gaps larger than this are treated as data errors or corporate actions
# (splits, symbol changes) and excluded from the evaluation.
MAX_PLAUSIBLE_GAP: float = 0.40

assert abs(sum(PREMARKET_WEIGHTS.values()) - 100.0) < 1e-9, "pre-market weights must sum to 100"
