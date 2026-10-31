# Testing and Reproducibility

## Running tests

From the repository root with dependencies installed:

```bash
python -m pytest -q
```

**Verified (2026-10-31):** **35 tests collected, 35 passed** (Python 3.14.6, local `.venv`).

Test modules:

| File | Focus |
|------|--------|
| `tests/test_data.py` | CSV validation, duplicates, missing values, short samples |
| `tests/test_metrics.py` | CAGR, vol, Sharpe (zero vol), beta, max DD, VaR/ES, rolling beta |
| `tests/test_hand_calculable.py` | Closed-form checks for TE, IR, Sortino, Sharpe with varying RF |
| `tests/test_regression.py` | Noise-free CAPM recovery; constant benchmark |
| `tests/test_regression_inference.py` | HAC lag rule, CI coverage, diagnostics export |
| `tests/test_regression_hac.py` | OLS/HAC coefficient identity |
| `tests/test_e2e.py` | Sample load, JSON export consistency, research summary content |

---

## Hand-calculable examples

Tests assert numeric equality (or tight tolerance) against manually derived values, for example:

- **CAGR:** three-period return series with explicit \(W_T\) and \(W_T^{252/3}-1\).
- **Volatility:** `std(ddof=1) * sqrt(252)` on a fixed quadruple of returns.
- **Tracking error / IR:** active return series with explicit sample std and mean.
- **CAPM (noise-free):** portfolio constructed as \(r_f + \alpha + \beta(e_b)\) with exact \(\hat\alpha, \hat\beta\).
- **VaR/ES:** empirical quantile and tail mean on a fixed six-point series.

See `tests/test_hand_calculable.py` and `tests/test_metrics.py` for exact fixtures.

---

## Edge cases covered

- Zero portfolio volatility → Sharpe `None`
- Constant benchmark excess → regression `None`
- Max drawdown with initial peak at wealth = 1
- Rolling beta NaN until full window; first valid estimate checked
- Duplicate dates → `DataValidationError`
- Returns \(\le -100\%\) rejected

---

## Deterministic outputs

- Bundled **`data/sample_returns.csv`:** synthetic, NumPy seed 42 (see `data/README.md`).
- **Historical case study:** not in git; reproducibility via `research/case_study_manifest.json` and `scripts/reproduce_case_study_analysis.py` after fetching CSV.

Application metrics are computed from uploaded or sample data only — no hardcoded dashboard values.

---

## Input validation behavior

`validate_and_align()`:

- Parses and lowercases column names
- Drops unparseable dates and missing returns (logged in `ValidationReport`)
- Rejects duplicate dates and impossible simple returns
- Enforces minimum observation count (default 2; app uses aligned series for analytics)

E2E tests cover malformed CSV, duplicates, and valid multi-row upload strings.

---

## Coverage gaps (honest)

Not exhaustively tested in pytest:

- Streamlit UI / browser interactions
- Plotly chart rendering
- Full statsmodels OLS text summary parsing
- `yfinance` fetch script (network; optional dependency)
- Every combination of sidebar parameters
- Formal property-based tests across random return paths

Regression integration relies on statsmodels; numerical tolerance tests use fixed seeds or deterministic algebra.

---

## Environment

- **Python:** `.python-version` specifies **3.14**; project developed and tested with 3.14.6.
- **Install:** `pip install -r requirements.txt` (Streamlit, pandas, NumPy, SciPy, statsmodels, Plotly, pytest).
- **Optional (case study fetch only):** `pip install yfinance` — not in `requirements.txt`.

---

## Case study verification script

After generating `data/case_study_qqq_spy.csv`:

```bash
python scripts/reproduce_case_study_analysis.py
```

Exit code 0 indicates agreement with `research/case_study_manifest.json` (metrics, regression, regimes) for the pinned SHA256 when data match the 2026-10-29 audit file.
