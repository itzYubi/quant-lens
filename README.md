# QuantLens — Portfolio Analytics & Risk Research

QuantLens is a **Portfolio Risk, Alpha Robustness, and Regime Analysis Lab**: a local (and Streamlit Cloud–ready) web app for uploading dated portfolio and benchmark returns and producing transparent performance, risk, CAPM regression (OLS + Newey–West HAC), rolling stability charts, descriptive regime splits, sensitivity checks, and a deterministic research summary.

> **Not financial advice.** All metrics are descriptive summaries of uploaded data.

## Features

- CSV upload with validation (columns, dates, duplicates, missing values, returns ≤ −100%)
- Configurable annual risk-free rate and periods-per-year (default 252)
- Cumulative growth and drawdown charts (Plotly)
- Metrics table: CAGR, ann. arithmetic return, vol, Sharpe, Sortino, beta, tracking error, IR, max drawdown, historical VaR/ES
- CAPM regression with OLS and HAC inference side by side
- Rolling beta, volatility, and Sharpe (configurable window)
- Descriptive benchmark up/down regime comparison
- Subperiod sensitivity and optional outlier diagnostic for alpha
- Download metrics as CSV/JSON; bundled **synthetic** sample CSV

## Screenshot

After launching the app locally, capture a screenshot of the Overview tab for your README or portfolio (not included in-repo).

## Prerequisites (macOS)

- Python **3.14** (project `.python-version` and local `.venv`; Streamlit Community Cloud — set Python 3.14 when available, or match your deployed runtime to the version you tested)
- `git` (optional)

## Setup

```bash
cd quant-lens
python3.14 -m venv .venv   # or: python3 -m venv .venv if it is 3.14
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
streamlit run app.py
```

Open the URL shown in the terminal (typically http://localhost:8501).

## CSV schema

| Column | Required | Description |
|--------|----------|-------------|
| `date` | Yes | Parseable date (e.g. `2023-01-03`) |
| `portfolio_return` | Yes | Simple decimal return (`0.01` = +1%) |
| `benchmark_return` | Yes | Simple decimal return |
| `risk_free_rate` | No | Per-period decimal by default; checkbox in UI if annual |

Rows are sorted by date and aligned; missing returns are dropped (not zero-filled).

## Methodology notes

- **Wealth:** \(W_t = \prod (1 + r_t)\), starting at 1.
- **CAGR:** \((W_T)^{252/n} - 1\) with configurable periods/year.
- **Ann. arithmetic return:** mean(\(r_t\)) × periods/year (distinct from CAGR).
- **Volatility:** sample std (ddof=1) × √periods/year.
- **Sharpe:** ann. mean excess return / ann. vol; periodic RF = annual RF / periods/year unless CSV column supplied.
- **Sortino:** MAR = 0 on simple returns; downside deviation uses excess returns below (MAR − RF).
- **VaR/ES:** empirical quantiles; UI reports **positive loss magnitude** at chosen confidence.
- **CAPM:** OLS of portfolio excess on benchmark excess; HAC (Newey–West) with lag rule `floor(4*(n/100)^(2/9))`.
- **Rolling metrics:** computed only after a full window (no look-ahead).

## Testing

```bash
python -m pytest -q
```

## Case study

The bundled `data/sample_returns.csv` is **synthetic** (fixed RNG seed) for offline demos and tests. A properly sourced historical case study (tickers, adjustments, retrieval date) is a documented **future improvement** — not included as real market data.

For a reproducible **historical** workflow (QQQ vs SPY example, optional download script), see [`research/HISTORICAL_CASE_STUDY.md`](research/HISTORICAL_CASE_STUDY.md). After fetching data locally, documented computed results are in [`research/CASE_STUDY_FINDINGS.md`](research/CASE_STUDY_FINDINGS.md) (regenerate numbers if you refetch).

## Deploy on Streamlit Community Cloud (free tier)

1. Push this repository to GitHub (no secrets, venv, or user uploads).
2. Go to [https://share.streamlit.io/](https://share.streamlit.io/) and connect the repo.
3. Set main file to `app.py` and deploy.
4. Verify the public URL loads and the sample dataset runs.

Free-tier limits, sleep behavior, and quotas may change; do not rely on this doc for SLA or performance guarantees.

**Local verification ≠ live deployment.** Confirm the hosted app yourself after deploy.

## Limitations

- Two return series only; no multi-factor or holdings data.
- OLS/HAC inference assumes a linear CAPM; structural breaks and non-normality are not fully modeled.
- Regime split is descriptive (benchmark sign), not a latent regime model.
- Cannot prove manager skill or identify unobserved exposures from returns alone.

## License

Use and modify for research and education.
