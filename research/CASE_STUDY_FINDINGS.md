# Historical case study findings (QQQ vs SPY)

**Status:** Generated from a one-off local fetch on **2026-10-29** (not part of CI). The CSV is gitignored (`data/case_study_qqq_spy.csv`); regenerate with `scripts/fetch_case_study_csv.py`.

## Data provenance

| Field | Value |
|-------|--------|
| Source | Yahoo Finance via `yfinance` |
| Portfolio proxy | QQQ (Nasdaq-100 ETF) |
| Benchmark | SPY (S&P 500 ETF) |
| Frequency | Daily simple returns from adjusted close (`auto_adjust=True`) |
| Script | `scripts/fetch_case_study_csv.py` |
| Default window | 2019-01-01 to 2024-12-31 (aligned sample ends **2024-12-30**) |
| Rows | 1508 aligned observations |
| Validation | No duplicate dates, no missing returns; portfolio return range ≈ −12.0% to +8.5% per day |

Risk-free rate in QuantLens run below: **4% annual** → periodic `0.04/252` (sidebar convention).

## Reproduce offline (no network)

```bash
# After CSV exists locally:
python -c "
from pathlib import Path
from quantlens.data import validate_and_align
from quantlens.metrics import compute_all_metrics
from quantlens.regression import run_capm_regression
d = validate_and_align(Path('data/case_study_qqq_spy.csv').read_bytes(), annual_risk_free_rate=0.04)
m = compute_all_metrics(d)
r = run_capm_regression(d)
print(m['portfolio_cagr'], r.annualized_alpha, r.inference[0].p_value_ols)
"
```

## Computed results (QuantLens, full sample)

| Measure | Value |
|---------|--------|
| Portfolio CAGR | 23.06% |
| Benchmark CAGR | 17.19% |
| Portfolio Sharpe | 0.811 |
| CAPM beta | 1.142 |
| Max drawdown | −35.12% |
| Historical VaR (95%, loss magnitude) | 2.45% |
| Expected shortfall (95%) | 3.60% |
| CAPM R² | 0.868 |
| Periodic α | 0.000155 |
| Annualized α (arith., α×252) | 3.91% |
| OLS p-value (α) | 0.281 |
| HAC p-value (α) | 0.282 |
| HAC lags | 7 (`floor(4×(n/100)^(2/9))`) |
| OLS F-statistic (joint model) | 9875.7 (p ≈ 0 under classical OLS F-test) |
| Durbin–Watson | 1.95 |

Rolling (60 obs., end of sample): rolling β ≈ 1.27; rolling ann. vol ≈ 17.4%.

Descriptive regimes (benchmark sign): **840** up days, **668** down days (not a latent regime model).

## Interpretation (descriptive only)

1. **Return level:** QQQ exhibited higher cumulative growth than SPY over this window, but the series are correlated (R² ≈ 0.87).
2. **Estimated alpha:** Point annualized CAPM α is positive (~3.9%), but **OLS and HAC p-values (~0.28) do not indicate precise evidence against α = 0 at the 5% level** under these specifications. This is not proof of skill or “genuine alpha.”
3. **Uncertainty:** HAC p-value is close to OLS here; conventional OLS F and DW (≈1.95) describe the classical fit only and are **not** HAC-robust.
4. **Rolling risk:** Rolling beta above 1 at the end of sample suggests time-varying market sensitivity; rolling vol shows evolving risk.
5. **Regimes:** Mean portfolio returns differ between benchmark-up and benchmark-down days; causal or predictive claims are not supported.
6. **Limitations:** Yahoo prices can revise; ETFs are not a managed portfolio; single-factor CAPM omits other exposures; one sample period.

## Relation to bundled synthetic data

`data/sample_returns.csv` remains **synthetic** (seed 42) for demos and automated tests. This case study uses **real downloaded** history and is optional.
