# Reproducible historical case study: passive equity vs. benchmark

This document describes how to build a **real** dated return series for QuantLens research. It is separate from the bundled synthetic sample (`data/sample_returns.csv`).

## Research question (illustrative)

“Over a fixed calendar window, how do estimated CAPM alpha, rolling beta, and tail risk for a simple equity proxy compare to a broad market benchmark on a risk-adjusted basis?”

QuantLens answers this **descriptively** from uploaded returns; it does not prove manager skill.

## Series definition

| Role | Suggested ticker | Rationale |
|------|------------------|-----------|
| Benchmark | `SPY` | US large-cap ETF, liquid proxy for market |
| Portfolio proxy | `QQQ` | Different equity exposure (example only; not a product recommendation) |

You may substitute any pair of total-return–consistent price series; document changes below.

## Data source and retrieval

- **Provider:** [Yahoo Finance](https://finance.yahoo.com/) via the optional `yfinance` Python package (not a runtime dependency of the Streamlit app).
- **Price field:** Adjusted close (splits/dividends reflected in adjusted prices).
- **Return:** Simple daily return \( r_t = P_t / P_{t-1} - 1 \).
- **Alignment:** Inner join on trading dates; drop rows with missing prices.

Record your run metadata when publishing results:

```text
Retrieval script: scripts/fetch_case_study_csv.py
Retrieval date:   YYYY-MM-DD (fill when you run)
Tickers:          QQQ (portfolio), SPY (benchmark)
Date range:       2019-01-01 to 2024-12-31 (default in script)
Risk-free:        Use sidebar annual rate or add a column from FRED (see below)
```

## Risk-free rate (optional extension)

The MVP UI uses a constant annual risk-free rate (default 4%, converted to daily as `annual/252`). For a published study you may merge a **per-period** risk-free series (e.g. FRED `DGS3MO` converted to daily) into column `risk_free_rate` and document that values are **annualized yields converted to daily simple rates**. Do not mix conventions without stating them.

## Reproduction steps

1. Create a virtual environment and install app dependencies plus fetch extras:

   ```bash
   pip install -r requirements.txt
   pip install yfinance
   ```

2. Run the fetch script from the repository root:

   ```bash
   python scripts/fetch_case_study_csv.py --output data/case_study_qqq_spy.csv
   ```

3. Validate locally:

   ```bash
   python -c "from pathlib import Path; from quantlens.data import validate_and_align; d=validate_and_align(Path('data/case_study_qqq_spy.csv').read_bytes()); print(d.report.n_rows_aligned, d.dates[0], d.dates[-1])"
   ```

4. Launch QuantLens, **disable** “Use bundled synthetic sample”, upload `data/case_study_qqq_spy.csv`.

5. Export JSON metrics and archive alongside this note for reproducibility.

## Output CSV schema

Same as the main app:

```csv
date,portfolio_return,benchmark_return
2020-01-02,0.0123,0.0045
```

Decimal returns; `0.01` = +1%.

## Limitations

- Yahoo data can be revised; always store retrieval date and script version.
- ETF returns ≠ a specific managed portfolio.
- OLS/HAC inference assumes a linear CAPM on excess returns; structural breaks are not modeled.
- This case study is **not** included in CI tests (network-dependent). Automated tests use synthetic series only.

## Status

- **Synthetic demo:** `data/sample_returns.csv` (seed 42) — used in app default and pytest.
- **Historical CSV:** generated locally via `scripts/fetch_case_study_csv.py` (gitignored as `data/case_study_*.csv`). See [`CASE_STUDY_FINDINGS.md`](./CASE_STUDY_FINDINGS.md) for a verified 2026-10-29 run.
