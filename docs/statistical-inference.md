# Statistical Inference — CAPM Regression

QuantLens estimates a single-factor CAPM on **aligned excess returns** using `statsmodels` OLS, then reports **classical** and **Newey–West HAC** inference side by side. Implementation: `quantlens/regression.py`.

---

## Model specification

For \(t = 1,\ldots,n\):

\[
e_{p,t} = \alpha + \beta \, e_{b,t} + \varepsilon_t
\]

where \(e_{p,t} = r_{p,t} - r_{f,t}\), \(e_{b,t} = r_{b,t} - r_{f,t}\).

Matrix form: \(y = X\theta + \varepsilon\), with \(y = e_p\), \(X = [\mathbf{1}, e_b]\), \(\theta = (\alpha, \beta)'\).

**Annualized alpha (display):** \(\alpha_{ann} = \alpha \times P\) (arithmetic scaling of the periodic intercept, not CAGR).

---

## OLS estimation

Coefficients are estimated by ordinary least squares:

\[
\hat\theta = (X'X)^{-1} X'y
\]

- **Code:** `sm.OLS(y, sm.add_constant(x)).fit()`
- **R-squared / Adj. R²:** from the same OLS fit (`rsquared`, `rsquared_adj`).

**Minimum sample:** regression returns `None` if \(n < 3\) or if \(\widehat{\text{Var}}(e_b) = 0\) (degenerate benchmark excess).

---

## Interpretation of \(\alpha\) and \(\beta\)

| Parameter | Meaning |
|-----------|---------|
| \(\hat\beta\) | Estimated linear exposure of portfolio excess returns to benchmark excess returns over the sample. |
| \(\hat\alpha\) | Estimated average portfolio excess return not explained by \(\beta \cdot e_b\) in the linear model (periodic). |

**Economic vs statistical:** A positive \(\hat\alpha\) is an **estimate**, not proof of skill. Multi-factor exposures, selection, and structural breaks are not modeled.

---

## Conventional OLS standard errors

Under classical assumptions (homoskedastic, uncorrelated errors):

- Standard errors, \(t\)-statistics, and p-values come from `model.bse`, `model.pvalues`.
- **95% confidence intervals:** `model.conf_int(alpha=0.05)` (default `confidence=0.95` in `run_capm_regression`).

**Diagnostics (OLS only, not HAC-robust):**

| Statistic | Role in QuantLens |
|-----------|-------------------|
| F-statistic / Prob(F) | Joint significance of regressors under classical linear model assumptions |
| Durbin–Watson | Residual first-order autocorrelation heuristic (~2 under no AR(1)) |

Stored in `RegressionDiagnostics` (`f_statistic`, `f_pvalue`, `durbin_watson`).

The expanded **statsmodels OLS summary** (Regression tab) also reports **Skew**, **Kurtosis**, **Jarque–Bera**, and **Omnibus / Prob(Omnibus)** for **residual normality** — descriptive on \(\hat\varepsilon\), not used to alter coefficient estimates.

---

## Newey–West HAC covariance

Financial return series often exhibit **heteroskedasticity** and **serial correlation**. Conventional OLS standard errors can understate uncertainty.

QuantLens computes HAC robust covariance:

```python
hac = model.get_robustcov_results(cov_type="HAC", maxlags=lags)
```

**Critical point:** HAC adjusts the **covariance matrix of \(\hat\theta\)** (thus HAC SEs, p-values, CIs). **\(\hat\alpha\) and \(\hat\beta\) are unchanged** from OLS.

HAC inference is exposed in parallel columns: `std_err_hac`, `p_value_hac`, `ci_low_hac`, `ci_high_hac`.

---

## HAC lag selection

Default lag count (when `hac_lags=None`):

\[
L = \left\lfloor 4 \left(\frac{n}{100}\right)^{2/9} \right\rfloor
\]

- **Code:** `default_hac_lags(n)`
- **Documented string:** `floor(4 * (n/100)^(2/9))` in UI and exports.

This is a common rule-of-thumb bandwidth, not a formal model-selection procedure. Users may override `hac_lags` in code paths that accept it; the Streamlit app uses the default rule.

**Unclear / not implemented:** Automatic lag selection by AIC/BIC, prewhitening, or Fama–MacBeth panels.

---

## Hypothesis testing and confidence intervals

For each coefficient, QuantLens reports:

- OLS and HAC **p-values** (two-sided, as provided by statsmodels)
- **95% CIs** under OLS and HAC covariance

The research summary (`quantlens/report.py`) prints numeric p-values and CIs; it does **not** label alpha “significant” without qualification.

---

## Statistical vs economic significance

- **Statistical:** Small p-values under a given covariance spec suggest the estimate is imprecisely compatible with zero **under that spec’s assumptions**.
- **Economic:** Magnitude of \(\hat\alpha_{ann}\), \(\hat\beta\), and confidence width matter for practical relevance.

A large \(\hat\alpha_{ann}\) with a wide CI or high HAC p-value indicates imprecise evidence.

---

## Limitations

1. **Single-factor CAPM** — omitted variables (size, value, momentum) bias \(\hat\alpha\).
2. **Linear, time-invariant** \(\beta\) in the full-sample regression (rolling beta is descriptive).
3. **Historical inference** — past regression does not forecast future alpha or beta.
4. **Risk-free specification** — constant or column \(r_f\); mis-specification affects excess returns.
5. **Non-normality / outliers** — OLS remains unbiased under standard exogeneity but inference can be fragile; HAC helps SEs, not structural model error.
6. **F and DW** — classical OLS diagnostics; not robustified by HAC in this implementation.

---

## Related

- [Methodology (metrics)](methodology.md)
- [Case study application](case-study-qqq-spy.md)
