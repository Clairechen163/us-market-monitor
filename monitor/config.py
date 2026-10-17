"""Central configuration: universe, benchmark, score weights and label thresholds.

Everything that defines the model lives here so that the scoring rules are
auditable in one place and the evaluation can refer to exactly the same
definitions the daily monitor uses.
"""

from __future__ import annotations

TICKERS: list[str] = ["KLAC", "ALAB", "SPCX", "TSLA", "VRT"]

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
