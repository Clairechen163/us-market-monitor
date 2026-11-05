"""Pre-market snapshot, run before the U.S. open.

Scores each ticker on how it is trading in the pre-market session
(04:00-09:30 ET) and writes:
    reports/premarket/premarket_YYYYMMDD.csv / .txt
    docs/premarket.md

Data: Alpaca's SIP feed when ALPACA_API_KEY_ID / ALPACA_API_SECRET_KEY are
set (it includes pre-market volume), otherwise Yahoo Finance (prices only:
Yahoo reports zero extended-hours volume, so the volume component is skipped).

Usage:
    python premarket_monitor.py                         # live, as of now
    python premarket_monitor.py --window 08:00-09:30    # skip unless NY time is inside
    python premarket_monitor.py --source synthetic --asof "2026-11-04 08:40"
"""

from __future__ import annotations

import argparse
import sys
from datetime import time
from pathlib import Path

import pandas as pd

from monitor import alpaca, config
from monitor.data import load as load_daily
from monitor.intraday import NY, daily_from_intraday, load_synthetic_intraday, load_yahoo_intraday
from monitor.premarket import COMPONENTS, PRE_OPEN, REG_OPEN, premarket_features, score_premarket

ROOT = Path(__file__).resolve().parent


def parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


DATA_NOTES = {
    "alpaca-sip": "Alpaca SIP feed (all U.S. exchanges, including pre-market volume; 15-minute delay).",
    "alpaca-iex": "Alpaca IEX feed: prices are real-time, but volume covers IEX trades only, "
                  "so pre-market RVOL is a partial measure.",
    "yahoo": "Yahoo Finance. Yahoo reports no pre-market volume, so the volume component is not "
             "scored (coverage 70%). Add Alpaca keys to score it.",
    "synthetic": "Synthetic demo data. Not real prices.",
}


def resolve_source(requested: str) -> str:
    if requested == "auto":
        return "alpaca" if alpaca.have_credentials() else "yahoo"
    return requested


def snapshot_cutoff(asof: pd.Timestamp, data_end: pd.Timestamp, snapshot: time) -> time:
    """Latest whole 5-minute mark with data, capped at the snapshot time."""
    if data_end.tz_convert(NY).normalize() < asof.normalize():
        return PRE_OPEN  # data does not reach today's pre-market yet
    available = data_end.tz_convert(NY).floor("5min").time()
    return max(PRE_OPEN, min(available, snapshot, REG_OPEN))


def _pct(x) -> str:
    return "–" if pd.isna(x) else f"{x * 100:+.1f}%"


def _num(x, f="{:.2f}") -> str:
    return "–" if pd.isna(x) else f.format(x)


def render_markdown(snap: pd.DataFrame, asof: pd.Timestamp, cutoff: time, source: str) -> str:
    rows = ["| Ticker | Score | Label | Pre-mkt | Prior close | Gap | Gap vs SPY | Gap / ATR | Pre-mkt RVOL | vs 20d high | Coverage |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t, r in snap.iterrows():
        rows.append(
            f"| **{t}** | {_num(r['pm_score'], '{:.1f}')} | {r['pm_label']} | {_num(r['pm_last'])} | "
            f"{_num(r['prev_close'])} | {_pct(r['gap'])} | {_pct(r['excess_gap'])} | "
            f"{_num(r['gap_atr'], '{:+.2f}')} | {_num(r['pm_rvol'])} | {_pct(r['vs_high20'])} | "
            f"{r['pm_coverage']:.0%} |")
    comp = ["| Ticker | " + " | ".join(f"{c.title()} (/{config.PREMARKET_WEIGHTS[c]:.0f})" for c in COMPONENTS) + " |",
            "|---|" + "---:|" * len(COMPONENTS)]
    for t, r in snap.iterrows():
        comp.append(f"| {t} | " + " | ".join(_num(r[f'pm_pts_{c}'], '{:.1f}') for c in COMPONENTS) + " |")
    return f"""# Pre-market snapshot

**Session:** {asof.date()} · **Pre-market bars through:** {cutoff.strftime('%H:%M')} ET
(run at {asof.strftime('%H:%M')} ET) · regenerated automatically on weekday mornings before the open.

**Data:** {DATA_NOTES.get(source, source)}

> Describes how each stock is trading before the open relative to its prior close, SPY and its
> own normal pre-market activity. Not a buy/sell recommendation. Whether it predicts the regular
> session is tested in [premarket_evaluation.md](premarket_evaluation.md).

## Signals

{chr(10).join(rows)}

## Score breakdown

{chr(10).join(comp)}

**Gap / ATR** expresses the gap over SPY in units of the stock's normal daily range (ATR14).
**Pre-mkt RVOL** compares pre-market volume so far with the average over the same part of the
morning on the previous {config.PREMARKET_RVOL_WINDOW} sessions. *Context* is the prior close's
[end-of-day score](dashboard.md). Volume points are cut by 75% when the stock is gapping down.
"""


def render_text(snap: pd.DataFrame, asof: pd.Timestamp, cutoff: time, source: str) -> str:
    lines = ["US MARKET MONITOR - PRE-MARKET",
             f"Session {asof.date()}  bars through {cutoff.strftime('%H:%M')} ET  source: {source}", ""]
    for t, r in snap.iterrows():
        lines.append(f"{t:<6} {_num(r['pm_score'], '{:.1f}'):>5} [{r['pm_label']}]  pre-mkt {_num(r['pm_last'])}  "
                     f"gap {_pct(r['gap'])} (vs SPY {_pct(r['excess_gap'])}, {_num(r['gap_atr'], '{:+.2f}')} ATR)  "
                     f"RVOL {_num(r['pm_rvol'])}  vs 20d high {_pct(r['vs_high20'])}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tickers", nargs="+", default=config.TICKERS)
    p.add_argument("--benchmark", default=config.BENCHMARK)
    p.add_argument("--source", choices=["auto", "alpaca", "yahoo", "synthetic"], default="auto",
                   help="auto = Alpaca if API keys are set, otherwise Yahoo")
    p.add_argument("--snapshot", type=parse_hhmm, default=parse_hhmm(config.PREMARKET_SNAPSHOT_TIME),
                   help="score pre-market bars that closed by this ET time (default %(default)s)")
    p.add_argument("--asof", help='New York time, e.g. "2026-11-04 08:40" (default: now)')
    p.add_argument("--window", help="HH:MM-HH:MM in ET; exit quietly if the run time is outside it")
    p.add_argument("--outdir", type=Path, default=ROOT / "reports" / "premarket")
    p.add_argument("--docs", type=Path, default=ROOT / "docs")
    args = p.parse_args(argv)

    asof = (pd.Timestamp(args.asof, tz=NY) if args.asof else pd.Timestamp.now(tz=NY)).floor("min")
    if args.window:
        lo, hi = (parse_hhmm(x) for x in args.window.split("-"))
        if not (lo <= asof.time() < hi):
            print(f"{asof:%H:%M} ET is outside {args.window}; nothing to do.")
            return 0
    today = asof.tz_localize(None).normalize()
    symbols = list(dict.fromkeys([*args.tickers, args.benchmark]))
    source = resolve_source(args.source)

    data_end = asof
    if source == "synthetic":
        intraday = load_synthetic_intraday(symbols, n_days=40, interval_minutes=5, asof=asof)
        daily = daily_from_intraday(intraday)
    else:
        intraday = None
        if source == "alpaca":
            data_end = min(asof, pd.Timestamp.now(tz=NY)) - alpaca.SIP_DELAY
            try:
                intraday, feed = alpaca.load_alpaca_intraday(
                    symbols, start=asof.normalize() - pd.Timedelta(days=40), end=data_end, timeframe="5Min")
                source = f"alpaca-{feed}"
            except alpaca.AlpacaError as e:
                if args.source == "alpaca":
                    raise
                print(f"WARNING: Alpaca request failed ({e}); falling back to Yahoo", file=sys.stderr)
                data_end = asof
        if intraday is None:
            source = "yahoo"
            intraday = load_yahoo_intraday(symbols, period="1mo", interval="5m")
        daily = load_daily(symbols, source="yahoo", period="2y")
    cutoff = snapshot_cutoff(asof, data_end, args.snapshot)
    # Context must come from completed sessions only.
    daily = {t: d[d.index < today] for t, d in daily.items()}

    # Short data summary so a failed run's log shows what the source returned.
    print(f"As of {asof:%Y-%m-%d %H:%M} ET; data: {source}; pre-market bars through {cutoff:%H:%M}")
    for t in symbols:
        i, d = intraday.get(t), daily.get(t)
        last = "none" if i is None or i.empty else f"{len(i)} bars, last {i.index[-1]:%m-%d %H:%M}"
        days = "none" if d is None or d.empty else f"{len(d)} days to {d.index[-1]:%Y-%m-%d}"
        print(f"  {t:<5} intraday: {last:<28} daily: {days}")
    print()

    feats = premarket_features(intraday, daily, args.tickers, args.benchmark, cutoff=cutoff)
    if cutoff <= PRE_OPEN or today not in feats.index.get_level_values("date"):
        print(f"No pre-market trading found for {today.date()} (weekend, holiday or too early).")
        return 0
    snap = feats.xs(today, level="date")
    snap = snap[snap["pm_last"].notna()]
    if snap.empty:
        print(f"No pre-market prices yet for {today.date()}.")
        return 0
    snap = snap.join(score_premarket(snap)).sort_values("pm_score", ascending=False, na_position="last")

    missing = [t for t in args.tickers if t not in snap.index]
    if missing:
        print(f"WARNING: no pre-market prices for {', '.join(missing)}", file=sys.stderr)

    args.outdir.mkdir(parents=True, exist_ok=True)
    suffix = "_synthetic" if source == "synthetic" else ""
    stem = args.outdir / f"premarket_{today:%Y%m%d}{suffix}"
    cols = ["pm_last", "prev_close", "gap", "excess_gap", "gap_atr", "pm_volume", "pm_rvol",
            "vs_high20", "ctx_score", *[f"pm_pts_{c}" for c in COMPONENTS], "pm_coverage", "pm_score", "pm_label"]
    out = snap[cols].copy()
    out.insert(0, "asof", asof.strftime("%Y-%m-%d %H:%M"))
    out.insert(1, "bars_through", cutoff.strftime("%H:%M"))
    out.insert(2, "source", source)
    out.to_csv(f"{stem}.csv", index_label="ticker", float_format="%.6g")
    text = render_text(snap, asof, cutoff, source)
    Path(f"{stem}.txt").write_text(text, encoding="utf-8")
    if source != "synthetic" or args.docs != ROOT / "docs":  # never publish synthetic data
        args.docs.mkdir(parents=True, exist_ok=True)
        (args.docs / "premarket.md").write_text(render_markdown(snap, asof, cutoff, source),
                                                encoding="utf-8")
    print(text)
    print(f"Wrote {stem}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
