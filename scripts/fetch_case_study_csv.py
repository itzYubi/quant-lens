#!/usr/bin/env python3
"""
Build a historical returns CSV for QuantLens (optional research use).

Requires: pip install yfinance pandas

Example:
  python scripts/fetch_case_study_csv.py --output data/case_study_qqq_spy.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Download adjusted-close returns for QuantLens case study.")
    parser.add_argument("--portfolio", default="QQQ", help="Portfolio proxy ticker")
    parser.add_argument("--benchmark", default="SPY", help="Benchmark ticker")
    parser.add_argument("--start", default="2019-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--output", type=Path, default=Path("data/case_study_qqq_spy.csv"))
    args = parser.parse_args()

    try:
        import yfinance as yf
    except ImportError as exc:
        raise SystemExit("Install yfinance: pip install yfinance") from exc

    px_p = yf.download(args.portfolio, start=args.start, end=args.end, auto_adjust=True, progress=False)["Close"]
    px_b = yf.download(args.benchmark, start=args.start, end=args.end, auto_adjust=True, progress=False)["Close"]
    if isinstance(px_p, pd.DataFrame):
        px_p = px_p.squeeze()
    if isinstance(px_b, pd.DataFrame):
        px_b = px_b.squeeze()

    df = pd.DataFrame({"port": px_p, "bench": px_b}).dropna()
    out = pd.DataFrame(
        {
            "date": df.index.strftime("%Y-%m-%d"),
            "portfolio_return": df["port"].pct_change(),
            "benchmark_return": df["bench"].pct_change(),
        }
    ).dropna()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Wrote {len(out)} rows to {args.output}")


if __name__ == "__main__":
    main()
