"""US Market Monitor: live dashboard.

Run locally:   streamlit run app/streamlit_app.py
Deploy:        Streamlit Community Cloud, main file app/streamlit_app.py,
               secrets ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY.

The scores use the same rules as the daily GitHub monitors (monitor/), with a
real-time price from Alpaca's free IEX feed and full-market volume up to
~15 minutes ago. See monitor/live.py for the details.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitor import alpaca, config, live  # noqa: E402
from monitor.intraday import NY  # noqa: E402

REPO = "https://github.com/Clairechen163/us-market-monitor"
LABEL_COLORS = {"STRONG PRICE/VOLUME": "#0b7d0b", "POSITIVE": "#2a78d6", "WATCH": "#b7790b",
                "WEAK": "#c03636", config.INSUFFICIENT_LABEL: "#6b6a65"}
PHASE_TITLES = {
    "premarket": "Pre-market · live",
    "regular": "Regular session · live",
    "after": "After the close",
    "closed": "Market closed",
}

st.set_page_config(page_title="US Market Monitor · Live", page_icon="📈", layout="wide")

# Streamlit Cloud keeps keys in st.secrets; the monitor package reads the environment.
try:
    for key in (alpaca.KEY_ENV, alpaca.SECRET_ENV):
        if key in st.secrets and not os.environ.get(key):
            os.environ[key] = str(st.secrets[key])
except Exception:  # no secrets file locally
    pass


def now_ny() -> pd.Timestamp:
    fixed = os.environ.get("MONITOR_ASOF")  # test hook: freeze the clock
    return pd.Timestamp(fixed, tz=NY) if fixed else pd.Timestamp.now(tz=NY)


# ------------------------------------------------------------------ data (cached)
@st.cache_data(ttl=20, show_spinner=False)
def get_trades(symbols: tuple[str, ...]) -> dict:
    return alpaca.load_latest_trades(list(symbols), feed="iex")


@st.cache_data(ttl=300, show_spinner=False)
def get_intraday(symbols: tuple[str, ...], now_key: str):
    now = pd.Timestamp(now_key)
    data_end = now - alpaca.SIP_DELAY
    data, feed = alpaca.load_alpaca_intraday(list(symbols), start=now.normalize() - pd.Timedelta(days=35),
                                             end=data_end, timeframe="5Min")
    return data, feed, data_end


@st.cache_data(ttl=900, show_spinner=False)
def get_daily(symbols: tuple[str, ...], now_key: str):
    now = pd.Timestamp(now_key)
    data, _ = alpaca.load_alpaca_daily(list(symbols), start=now - pd.DateOffset(years=2),
                                       end=now - alpaca.SIP_DELAY)
    return data


# ------------------------------------------------------------------ rendering
def pct(s):
    return s * 100


def score_chart(df: pd.DataFrame, score_col: str, label_col: str):
    d = df[[score_col, label_col]].reset_index()
    d.columns = ["Ticker", "Score", "Label"]
    d["Text"] = d["Score"].map(lambda v: "" if pd.isna(v) else f"{v:.0f}")
    order = d.sort_values("Score", ascending=False, na_position="last")["Ticker"].tolist()
    base = alt.Chart(d).encode(
        y=alt.Y("Ticker:N", sort=order, title=None, axis=alt.Axis(labelOverlap=False)),
        x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(values=[0, 45, 60, 75, 100]),  # ticks at the label cut-offs
                title="Score (0–100) · WEAK < 45 ≤ WATCH < 60 ≤ POSITIVE < 75 ≤ STRONG"),
        tooltip=["Ticker", alt.Tooltip("Score:Q", format=".1f"), "Label"],
    )
    bars = base.mark_bar(cornerRadiusEnd=4, size=14).encode(
        color=alt.Color("Label:N", scale=alt.Scale(domain=list(LABEL_COLORS), range=list(LABEL_COLORS.values())),
                        legend=alt.Legend(title=None, orient="top")))
    text = base.mark_text(align="left", dx=4).encode(text="Text:N")
    return (bars + text).properties(height=alt.Step(24))


def render_table(df: pd.DataFrame, phase: str) -> None:
    cfg = st.column_config
    if phase == "premarket":
        t = pd.DataFrame({
            "Score": df["pm_score"], "Label": df["pm_label"], "Price": df["pm_last"],
            "Price source": df.get("price_source"), "Gap %": pct(df["gap"]),
            "Gap vs SPY %": pct(df["excess_gap"]), "Gap / ATR": df["gap_atr"],
            "Pre-mkt RVOL": df["pm_rvol"], "vs 20d high %": pct(df["vs_high20"]),
            "Coverage %": pct(df["pm_coverage"]),
        })
    elif phase == "regular":
        t = pd.DataFrame({
            "Score": df["score"], "Label": df["label"], "Price": df["price"],
            "Price source": df.get("price_source"), "Change %": pct(df["price"] / df["prev_close"] - 1),
            "RVOL since open": df["rvol20"], "RSI14": df["rsi14"],
            "vs 20d high %": pct(df["breakout_pct"]), "Coverage %": pct(df["coverage"]),
        })
    else:
        t = pd.DataFrame({
            "Score": df["score"], "Label": df["label"], "Close": df["Close"],
            "1d %": pct(df["ret_1d"]), "RVOL20": df["rvol20"], "RSI14": df["rsi14"],
            "vs 20d high %": pct(df["breakout_pct"]), "Coverage %": pct(df["coverage"]),
        })
    t.index.name = "Ticker"
    t["Label"] = t["Label"].replace({"STRONG PRICE/VOLUME": "STRONG", config.INSUFFICIENT_LABEL: "NO DATA"})
    fmt = {c: cfg.NumberColumn(format="%.1f") for c in t.columns if "%" in c}
    fmt.update({
        "Score": cfg.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
        "Price": cfg.NumberColumn(format="%.2f"), "Close": cfg.NumberColumn(format="%.2f"),
        "Gap / ATR": cfg.NumberColumn(format="%.2f"), "Pre-mkt RVOL": cfg.NumberColumn(format="%.2f"),
        "RVOL since open": cfg.NumberColumn(format="%.2f"), "RVOL20": cfg.NumberColumn(format="%.2f"),
        "RSI14": cfg.NumberColumn(format="%.1f"),
    })
    st.dataframe(t, column_config=fmt, width="stretch", height=36 * (len(t) + 1) + 4)


def freshness(df: pd.DataFrame, data_end: pd.Timestamp, feed: str, now: pd.Timestamp) -> str:
    parts = []
    if "price_time" in df and df["price_time"].notna().any():
        latest = pd.to_datetime(df["price_time"]).max().tz_convert(NY)
        src = "IEX real-time" if (df.get("price_source") == "IEX real-time").any() else "all exchanges"
        parts.append(f"Prices: {src}, latest trade {latest:%H:%M:%S} ET")
    vol = ("all U.S. exchanges" if feed == "sip" else "IEX only") + f" through {data_end.tz_convert(NY):%H:%M} ET"
    if feed == "sip":
        vol += " (free-plan 15-minute delay)"
    parts.append(f"Volume: {vol}")
    parts.append(f"Updated {now:%H:%M:%S} ET")
    return " · ".join(parts)


# ------------------------------------------------------------------ page
st.title("US Market Monitor · Live")
st.caption("A transparent price/volume score for U.S. stocks, recomputed from live data each time this page "
           f"refreshes. Same rules as the [daily monitors on GitHub]({REPO}).")

if not alpaca.have_credentials():
    st.error("Alpaca API keys are missing. Add `ALPACA_API_KEY_ID` and `ALPACA_API_SECRET_KEY` to this "
             "app's secrets (Streamlit Cloud → app → Settings → Secrets) or to your environment.")
    st.stop()

with st.sidebar:
    tickers = st.multiselect("Tickers", config.TICKERS, default=config.TICKERS)
    auto = st.toggle("Auto-refresh every minute", value=True)
    st.markdown(f"[Code and weekly evaluation on GitHub]({REPO})")
    st.caption("Not investment advice.")


@st.fragment(run_every=60 if auto else None)
def live_panel() -> None:
    if not tickers:
        st.info("Pick at least one ticker in the sidebar.")
        return
    now = now_ny()
    symbols = tuple(dict.fromkeys([*tickers, config.BENCHMARK]))
    key = now.floor("5min").isoformat()
    try:
        with st.spinner("Fetching market data…"):
            intraday, feed, data_end = get_intraday(symbols, key)
            daily = get_daily(symbols, now.floor("15min").isoformat())
            trades = get_trades(symbols) if live.market_phase(now) in ("premarket", "regular") else {}
    except alpaca.AlpacaError as e:
        st.error(f"Alpaca request failed: {e}")
        return

    phase = live.market_phase(now)
    df = pd.DataFrame()
    if phase == "premarket":
        df, cutoff = live.live_premarket(intraday, daily, trades, list(tickers), config.BENCHMARK, now, data_end)
        score_col, label_col = "pm_score", "pm_label"
    elif phase == "regular":
        df, cutoff = live.live_intraday(intraday, daily, trades, list(tickers), config.BENCHMARK, now, data_end)
        score_col, label_col = "score", "label"
    if df.empty:
        if phase in ("premarket", "regular"):
            st.info("No trading recorded yet today (holiday, or the session has just started). "
                    "Showing the latest close instead.")
            phase = "closed"
        df = live.latest_close(daily, list(tickers), config.BENCHMARK, now, data_end)
        score_col, label_col = "score", "label"

    title = PHASE_TITLES[phase]
    if phase in ("after", "closed") and "date" in df:
        title += f" · end-of-day score for {pd.to_datetime(df['date']).max():%a %d %b %Y}"
    st.subheader(title)
    if phase in ("premarket", "regular"):
        st.caption(freshness(df, data_end, feed, now))
    else:
        st.caption(f"Updated {now:%H:%M:%S} ET")

    render_table(df, phase)
    st.altair_chart(score_chart(df, score_col, label_col), width="stretch")


live_panel()

with st.expander("How the live score works"):
    st.markdown(f"""
- **Before the open (04:00–09:30 ET)** the page shows the pre-market score: the gap from yesterday's close
  relative to SPY (in ATR units), pre-market volume against the same part of the morning on the last
  {config.PREMARKET_RVOL_WINDOW} sessions, the price against its 20-day high, and yesterday's end-of-day score.
- **During the session (09:30–16:00 ET)** it shows the end-of-day score as if the session ended now. Volume
  since 09:30 is compared with the same window on the previous 20 sessions, because a full-day comparison
  would always look low mid-session.
- **After the close** it shows the end-of-day score for the latest completed session.
- **Data.** Prices are real-time trades from the IEX exchange (Alpaca's free plan); volume covers every
  U.S. exchange but runs about 15 minutes behind. If the latest full-market bar is newer than the last IEX
  trade, its price is used. Daily history is split-adjusted Alpaca data, so scores can differ slightly
  from the GitHub badges, which use Yahoo Finance.
- **What the score is not.** The [weekly evaluation]({REPO}#key-findings) finds no evidence that these scores
  predict returns. They describe how a stock is trading right now; they are not a forecast or a
  recommendation.
""")
