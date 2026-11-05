"""Intraday bars from Alpaca Market Data API v2 (free "Basic" plan).

Why Alpaca for the pre-market: Yahoo reports zero volume for extended-hours
bars, so pre-market volume cannot be measured from it. Alpaca's SIP feed
aggregates trades from every U.S. exchange, including the pre-market
session from 04:00 ET, and the free plan serves SIP history back to 2016
except for the most recent 15 minutes.

Credentials come from the environment (GitHub Actions secrets):
    ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY

If the account cannot read SIP data, the loader falls back to the IEX feed,
which is real-time but covers only trades on IEX (a few percent of volume);
the returned ``feed`` says which one was used.
"""

from __future__ import annotations

import os
import time as _time

import pandas as pd

from .config import LISTING_DATES
from .data import trim_to_listing
from .intraday import NY

BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
KEY_ENV, SECRET_ENV = "ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"
# Free plan: the most recent 15 minutes of SIP data are not available.
SIP_DELAY = pd.Timedelta(minutes=16)


class AlpacaError(RuntimeError):
    pass


def have_credentials() -> bool:
    return bool(os.environ.get(KEY_ENV) and os.environ.get(SECRET_ENV))


def _rfc3339(ts: pd.Timestamp) -> str:
    return pd.Timestamp(ts).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def _get(session, params: dict, headers: dict, max_retries: int = 4) -> dict:
    for attempt in range(max_retries):
        r = session.get(BARS_URL, params=params, headers=headers, timeout=60)
        if r.status_code == 429:  # rate limited: back off and try again
            _time.sleep(float(r.headers.get("Retry-After", 2 ** attempt)))
            continue
        if r.status_code != 200:
            try:
                msg = r.json().get("message", r.text)
            except ValueError:
                msg = r.text
            raise AlpacaError(f"HTTP {r.status_code}: {msg}")
        return r.json()
    raise AlpacaError("rate limited repeatedly; giving up")


def _fetch(symbols, start, end, timeframe, feed, adjustment, session, headers) -> dict[str, pd.DataFrame]:
    params = {
        "symbols": ",".join(symbols), "timeframe": timeframe,
        "start": _rfc3339(start), "end": _rfc3339(end),
        "limit": 10000, "adjustment": adjustment, "feed": feed, "sort": "asc",
    }
    rows: dict[str, list] = {s: [] for s in symbols}
    while True:
        payload = _get(session, params, headers)
        for sym, bars in (payload.get("bars") or {}).items():
            rows.setdefault(sym, []).extend(bars)
        token = payload.get("next_page_token")
        if not token:
            break
        params["page_token"] = token

    out = {}
    for sym, bars in rows.items():
        if not bars:
            continue
        df = pd.DataFrame(bars)
        idx = pd.DatetimeIndex(pd.to_datetime(df["t"], utc=True)).tz_convert(NY).as_unit("ns")
        frame = pd.DataFrame({
            "Open": df["o"].to_numpy(), "High": df["h"].to_numpy(), "Low": df["l"].to_numpy(),
            "Close": df["c"].to_numpy(), "Volume": df["v"].to_numpy(),
        }, index=idx).astype(float)
        frame = frame[~frame.index.duplicated(keep="last")].sort_index()
        out[sym] = frame
    return out


def load_alpaca_intraday(
    symbols: list[str],
    start: pd.Timestamp,
    end: pd.Timestamp,
    timeframe: str = "5Min",
    feed: str = "sip",
    adjustment: str = "split",
    session=None,
) -> tuple[dict[str, pd.DataFrame], str]:
    """Bars for all sessions (04:00-20:00 ET) between start and end.

    Returns (data, feed_used). Prices are split-adjusted so they line up with
    Yahoo's split-adjusted daily history used for context.
    """
    if not have_credentials():
        raise AlpacaError(f"set {KEY_ENV} and {SECRET_ENV} to use Alpaca data")
    if session is None:
        import requests

        session = requests.Session()
    headers = {"APCA-API-KEY-ID": os.environ[KEY_ENV], "APCA-API-SECRET-KEY": os.environ[SECRET_ENV]}
    try:
        data = _fetch(symbols, start, end, timeframe, feed, adjustment, session, headers)
        used = feed
    except AlpacaError as e:
        # e.g. 403 "subscription does not permit querying recent SIP data"
        if not (feed == "sip" and any(f"HTTP {c}" in str(e) for c in (403, 422))):
            raise
        data = _fetch(symbols, start, end, timeframe, "iex", adjustment, session, headers)
        used = "iex"
    return trim_to_listing(data, LISTING_DATES), used
