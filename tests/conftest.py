import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from monitor.data import load_synthetic  # noqa: E402


@pytest.fixture(scope="session")
def synthetic():
    # Index 0 and 4 are "young" listings (short history), like a recent IPO.
    return load_synthetic(["SPCX", "KLAC", "ALAB", "TSLA", "VRT", "SPY"],
                          n_days=900, seed=11, end="2026-10-16")
