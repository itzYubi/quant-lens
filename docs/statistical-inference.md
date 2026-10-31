# Statistical Inference — CAPM Regression

QuantLens estimates a single-factor CAPM on **aligned excess returns** using `statsmodels` OLS, then reports **classical** and **Newey–West HAC** inference side by side. Implementation: `quantlens/regression.py`.

---

## Model specification

For each period t = 1, …, n:

```text
e_p,t = alpha + beta × e_b,t + epsilon_t
```

where e_p,t = r_p,t - r_f,t and e_b,t = r_b,t - r_f,t.

Matrix form: y = X·theta + epsilon, with y = portfolio excess, X = [1, e_b], theta = (alpha, beta)'.

**Annualized alpha (display):** alpha_ann = alpha × P (arithmetic scaling of the periodic intercept, not CAGR).

---

## OLS estimation

```text
theta_hat = (X'X)^(-1) X'y
```

- **Code:** `sm.OLS(y, sm.add_constant(x)).fit()`
- **R² / Adj. R²:** from the same OLS fit.

**Minimum sample:** returns `None` if n < 3 or benchmark excess variance is zero.

---

## Interpretation of alpha and beta

| Parameter | Meaning |
|-----------|---------|
| beta (OLS) | Estimated linear exposure of portfolio excess to benchmark excess. |
| alpha (OLS intercept) | Estimated average portfolio excess not explained by beta × e_b in the linear model (periodic). |

A positive alpha estimate is not proof of skill. Multi-factor exposures and structural breaks are not modeled.

---

## Conventional OLS standard errors

Under homoskedastic, uncorrelated errors:

- SEs, t-stats, and p-values from `model.bse`, `model.pvalues`
- 95% CIs from `model.conf_int(alpha=0.05)` (default confidence = 0.95)

**Diagnostics (OLS only, not HAC-robust):**

| Statistic | Role |
|-----------|------|
| F-statistic / Prob(F) | Joint significance of regressors under classical LM assumptions |
| Durbin–Watson | Residual autocorrelation heuristic (~2 if little AR(1)) |

Stored in `RegressionDiagnostics`.

The expanded statsmodels OLS summary also reports **Skew**, **Kurtosis**, **Jarque–Bera**, and **Omnibus / Prob(Omnibus)** on **residuals** — descriptive only; coefficients are unchanged.

---

## Newey–West HAC covariance

```python
hac = model.get_robustcov_results(cov_type="HAC", maxlags=lags)
```

**Critical point:** HAC changes the **covariance matrix of theta_hat** (hence HAC SEs, p-values, CIs). **alpha_hat and beta_hat stay the same as OLS.**

Parallel columns in the UI: `std_err_hac`, `p_value_hac`, `ci_low_hac`, `ci_high_hac`.

---

## HAC lag selection

When `hac_lags=None`:

```text
L = floor( 4 × (n / 100)^(2/9) )
```

- **Code:** `default_hac_lags(n)`
- **Examples:** n = 300 → L = 5; n = 1,508 → L = 7

Rule of thumb for statsmodels `maxlags`, not formal AIC/BIC lag selection. The Streamlit app uses this default.

---

## Hypothesis testing and confidence intervals

QuantLens reports OLS and HAC p-values and 95% CIs per coefficient. The research summary prints numeric values; it does not label alpha “significant” without qualification.

---

## Statistical vs economic significance

- **Statistical:** p-values assess compatibility with zero under stated assumptions and covariance estimate.
- **Economic:** Magnitude of alpha_ann, beta, and CI width matter for practical interpretation.

---

## Limitations

1. Single-factor CAPM — omitted variables can bias alpha.
2. Full-sample beta is constant in the regression; rolling beta is descriptive only.
3. In-sample inference does not forecast future alpha or beta.
4. Risk-free mis-specification affects excess returns.
5. F and Durbin–Watson are classical OLS; not HAC-robust in this app.

---

## Related

- [Methodology (metrics)](methodology.md)
- [Case study application](case-study-qqq-spy.md)
