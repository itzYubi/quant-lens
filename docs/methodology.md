# QuantLens Methodology

This document defines the **mathematical conventions implemented in code**. All formulas below match `quantlens/metrics.py`, `quantlens/data.py`, and related modules unless noted.

**Global conventions**

| Setting | Default | Implementation |
|--------|---------|----------------|
| Return type | Simple decimal returns | `r_t`; `0.01` = +1% |
| Wealth index | W₀ = 1, W_t = product of (1 + r_s) | `cumulative_wealth()` |
| Periods per year | P = 252 | UI / `periods_per_year` |
| Risk-free (UI) | Annual rate R_f_ann | Periodic: r_f = R_f_ann / P | `annual_to_periodic_rate()` |
| Sample variance / std | `ddof=1` | pandas / NumPy |
| Alignment | Sort by date; drop missing returns; no zero-fill | `validate_and_align()` |

---

## CAGR and annualized arithmetic return

**CAGR** (portfolio or benchmark):

```text
W_T = product over t of (1 + r_t)
CAGR = W_T^(P/n) - 1
```

- **Interpretation:** Constant annual simple rate that compounds to the same terminal wealth over n periods.
- **Assumptions:** Simple returns; W_T > 0.
- **Edge cases:** Returns `None` if n = 0 or W_T ≤ 0.
- **Code:** `cagr()`, `cumulative_growth_final()`

**Annualized arithmetic return:**

```text
r_ann = mean(r_t) × P
```

- **Interpretation:** Scales the sample mean period return; **not** CAGR.
- **Edge cases:** Defined for n ≥ 1.
- **Code:** `annualized_arithmetic_return()`

---

## Annualized volatility

```text
sigma_ann = std(r_1, ..., r_n; ddof=1) × sqrt(P)
```

- **Interpretation:** Dispersion of **raw** periodic returns (portfolio or benchmark headline vol).
- **Edge cases:** `None` if n < 2.
- **Code:** `annualized_volatility()`

---

## Excess, active, and benchmark-relative quantities

- **Excess return:** e_t = r_t - r_f,t — `excess_returns()`
- **Active return:** a_t = r_p,t - r_b,t — `active_returns()`

---

## Sharpe ratio

```text
Sharpe = (mean(e_t) × P) / sigma_ann(excess)
```

where `sigma_ann(excess)` is the annualized sample std of **excess** returns.

- **Code:** `sharpe_ratio()`

---

## Sortino ratio

Numerator: mean(e_t) × P.

Downside: MAR = 0 on **simple** returns (configurable `target_periodic`). Excess MAR threshold m_t = MAR - r_f,t. Shortfall observations satisfy e_t - m_t < 0; downside deviation is the sample std of those shortfalls, times sqrt(P).

```text
Sortino = (mean(e_t) × P) / sigma_down,ann
```

- **Code:** `sortino_ratio()`; `sortino_target_periodic` = 0.0 in metrics dict.

---

## Beta (CAPM, sample)

```text
beta = Cov_sample(e_p, e_b) / Var_sample(e_b)
```

with e_p = r_p - r_f, e_b = r_b - r_f.

- **Code:** `beta()` — same excess definition as CAPM; OLS regression beta may differ slightly because of the fitted intercept.

---

## Tracking error and information ratio

```text
TE = std(a_t; ddof=1) × sqrt(P)
IR = (mean(a_t) × P) / TE
```

- **Code:** `tracking_error()`, `information_ratio()`

---

## Maximum drawdown

Wealth W_t from cumulative product. Running peak = cummax(W). Drawdown D_t = W_t / peak_t - 1.

```text
MDD = min_t(D_t)
```

Initial W_0 = 1 counts as a peak.

- **Code:** `max_drawdown()`, `drawdown_series()`

---

## Historical Value at Risk (VaR)

For confidence γ (e.g. 0.95), quantile level q = 1 - γ. Empirical quantile r_q = Q_q(r).

- **UI (`as_positive_loss=True`):** report max(-r_q, 0) as a **positive loss magnitude**.
- **Code:** `historical_var()`

---

## Expected shortfall (CVaR / ES)

Tail mean of returns at or below the VaR return threshold; UI uses the same positive-loss convention as VaR.

- **Code:** `expected_shortfall()`

---

## Rolling beta, volatility, and Sharpe

For window size w, at index i ≥ w-1, use only observations in [i-w+1, i].

- **Rolling beta:** CAPM beta on excess returns in window — `rolling_beta()`; NaN until the window is full.
- **Rolling vol:** std of **raw** returns in window × sqrt(P) — `rolling_volatility()`.
- **Rolling Sharpe:** (mean excess in window × P) / (ann. std of excess in window) — `rolling_sharpe()`.

**No look-ahead:** first valid index is i = w - 1.

---

## Data validation (inputs)

See `quantlens/data.py`: required columns `date`, `portfolio_return`, `benchmark_return`; optional `risk_free_rate`; duplicate dates rejected; returns must be > -1; missing returns dropped with report.

---

## Related documents

- [Statistical inference (CAPM)](statistical-inference.md)
- [QQQ vs SPY case study](case-study-qqq-spy.md)
- [Testing and reproducibility](testing.md)
