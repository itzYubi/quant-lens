# Case Study: QQQ vs SPY (2019–2024)

This document describes an **optional historical illustration** using publicly available ETF prices. It is **not** the bundled synthetic demo (`data/sample_returns.csv`). Full return history is **not committed** to git (see `.gitignore`); reviewers reproduce via the fetch script and verification manifest.

---

## 1. Research objective

Descriptive question: over a fixed calendar window, how do QQQ (portfolio proxy) and SPY (benchmark) compare on cumulative performance, risk, CAPM linear exposure, rolling risk, and simple benchmark up/down splits? Can estimated alpha be distinguished from zero under OLS and HAC inference?

This is **not** a trading strategy backtest or proof of skill.

---

## 2. Data sources and sample period

| Item | Detail |
|------|--------|
| Source | Yahoo Finance via `yfinance` (optional script) |
| Portfolio | **QQQ** (Nasdaq-100 ETF) |
| Benchmark | **SPY** (S&P 500 ETF) |
| Price | Adjusted close (`auto_adjust=True`) |
| Returns | Daily simple `pct_change` after inner join on dates |
| Requested window | 2019-01-01 to 2024-12-31 |
| Aligned sample | **2019-01-03** to **2024-12-30**, **n = 1508** |
| Retrieval audit | 2026-10-29 (see `research/case_study_manifest.json`) |

**Reproduce data:**

```bash
pip install yfinance   # not in requirements.txt
python scripts/fetch_case_study_csv.py --output data/case_study_qqq_spy.csv
```

**Verify analysis (offline):**

```bash
python scripts/reproduce_case_study_analysis.py
```

Expected SHA256 for the 2026-10-29 file: `f3b19184136da53ecd01c29b198362544ce0480e144e125a0c0d450b6bdd7e53`. A different hash after refetch may indicate Yahoo revisions — compare metrics to manifest with caution.

---

## 3. QuantLens settings

| Parameter | Value |
|-----------|--------|
| Annual risk-free rate | 4% (decimal 0.04) |
| Periodic RF | `0.04 / 252` |
| Periods per year | 252 |
| VaR / ES confidence | 95% |
| Rolling window | 60 observations |

---

## 4. Performance and risk metrics (full sample)

Values below were **recomputed locally** with `reproduce_case_study_analysis.py` (exit code 0 on 2026-10-31) and match `research/case_study_manifest.json`.

| Metric | Value |
|--------|------:|
| Portfolio (QQQ) CAGR | 23.06% |
| Benchmark (SPY) CAGR | 17.19% |
| Portfolio Sharpe | 0.811 |
| Beta (sample CAPM) | 1.142 |
| Max drawdown | −35.12% |
| Historical VaR (95%, loss mag.) | 2.45% |
| Expected shortfall (95%) | 3.60% |

---

## 5. CAPM regression results

| Quantity | Value |
|----------|------:|
| R² | 0.868 |
| Periodic \(\hat\alpha\) | 0.000155 |
| Annualized \(\hat\alpha\) (×252) | 3.91% |
| \(\hat\beta\) | 1.142 |
| Durbin–Watson (OLS) | 1.95 |

---

## 6. OLS vs HAC inference (alpha)

| Method | p-value (α) |
|--------|------------:|
| OLS | 0.281 |
| HAC (Newey–West, **7** lags) | 0.282 |

**Interpretation:** Point \(\hat\alpha_{ann}\) is positive, but **neither** OLS nor HAC rejects \(\alpha=0\) at conventional 5% levels. This does not support a strong claim of nonzero alpha in this single-factor specification.

HAC lag: \(L = \lfloor 4 (n/100)^{2/9} \rfloor = 7\) for \(n=1508\).

---

## 7. Rolling statistics (end of sample)

| Series | Last valid value (60-day window) |
|--------|----------------------------------:|
| Rolling beta | 1.27 |
| Rolling ann. volatility | 17.43% |

---

## 8. Regime and subperiod sensitivity

**Descriptive regimes** (benchmark return sign):

| Regime | Days |
|--------|-----:|
| Benchmark ≥ 0 | 840 |
| Benchmark < 0 | 668 |

Not a latent regime model; no causal interpretation.

**First vs second half** (split at n/2, requires n ≥ 40):

| Half | Ann. α (CAPM) | β |
|------|--------------:|---:|
| First | 8.85% | 1.05 |
| Second | 0.13% | 1.29 |

Subperiod estimates illustrate **instability** of \(\hat\alpha\) across time; they are not independent out-of-sample tests.

---

## 9. Limitations

- Yahoo data can revise; ETFs ≠ managed portfolios.
- Single-factor CAPM; growth/tech exposure not isolated.
- Constant RF approximation; no transaction costs or taxes.
- In-sample statistics only; no walk-forward validation.
- Regime splits are descriptive, not predictive.

---

## Related files

- [`research/HISTORICAL_CASE_STUDY.md`](../research/HISTORICAL_CASE_STUDY.md) — workflow overview
- [`research/CASE_STUDY_FINDINGS.md`](../research/CASE_STUDY_FINDINGS.md) — narrative summary (2026-10-29)
- [`research/case_study_manifest.json`](../research/case_study_manifest.json) — reference numerics
- [`data/case_study_csv_format_example.csv`](../data/case_study_csv_format_example.csv) — schema only (not real history)
