# QuantLens Methodology

This document defines the **mathematical conventions implemented in code**. All formulas below match `quantlens/metrics.py`, `quantlens/data.py`, and related modules unless noted.

**Global conventions**

| Setting | Default | Implementation |
|--------|---------|----------------|
| Return type | Simple decimal returns | \(r_t\); `0.01` = +1% |
| Wealth index | \(W_0 = 1\), \(W_t = \prod_{s \le t}(1+r_s)\) | `cumulative_wealth()` |
| Periods per year | \(P = 252\) | UI / `periods_per_year` |
| Risk-free (UI) | Annual rate \(R_f^{ann}\) | Periodic: \(r_f = R_f^{ann}/P\) | `annual_to_periodic_rate()` |
| Sample variance / std | `ddof=1` | pandas / NumPy |
| Alignment | Sort by date; drop missing returns; no zero-fill | `validate_and_align()` |

---

## CAGR and annualized arithmetic return

**CAGR** (portfolio or benchmark):

\[
W_T = \prod_{t=1}^{n}(1+r_t), \quad \text{CAGR} = W_T^{P/n} - 1
\]

- **Interpretation:** Constant annual simple rate that compounds to the same terminal wealth over \(n\) periods.
- **Assumptions:** Simple returns; \(W_T > 0\).
- **Edge cases:** Returns `None` if \(n=0\), \(W_T \le 0\).
- **Code:** `cagr()`, `cumulative_growth_final()`

**Annualized arithmetic return:**

\[
\bar{r}_{ann} = \left(\frac{1}{n}\sum_{t=1}^{n} r_t\right) \times P
\]

- **Interpretation:** Scales the sample mean period return; **not** CAGR.
- **Edge cases:** Defined for \(n \ge 1\).
- **Code:** `annualized_arithmetic_return()`

---

## Annualized volatility

\[
\sigma_{ann} = \text{std}(r_1,\ldots,r_n; \text{ddof=1}) \times \sqrt{P}
\]

- **Interpretation:** Dispersion of **raw** periodic returns (portfolio or benchmark headline vol).
- **Assumptions:** Stationarity not required; descriptive sample statistic.
- **Edge cases:** `None` if \(n < 2\).
- **Code:** `annualized_volatility()`

---

## Excess, active, and benchmark-relative quantities

- **Excess return:** \(e_t = r_t - r_{f,t}\) — `excess_returns()`
- **Active return:** \(a_t = r_{p,t} - r_{b,t}\) — `active_returns()`

---

## Sharpe ratio

\[
\text{Sharpe} = \frac{\bar{e} \times P}{\sigma_{ann}(e)}
\]

where \(\sigma_{ann}(e)\) is the annualized sample std of **excess** returns.

- **Interpretation:** Excess return per unit of excess-return volatility.
- **Assumptions:** Constant or row-wise \(r_f\); uses same \(P\) for mean and vol.
- **Edge cases:** `None` if excess vol is 0 or undefined.
- **Code:** `sharpe_ratio()`

---

## Sortino ratio

Numerator: \(\bar{e} \times P\).

Downside: let MAR = 0 on **simple** returns (configurable `target_periodic`). Define excess MAR threshold \(m_t = \text{MAR} - r_{f,t}\). Shortfall observations are \(e_t - m_t < 0\); downside deviation is the sample std of those shortfalls, times \(\sqrt{P}\).

\[
\text{Sortino} = \frac{\bar{e} \times P}{\sigma_{down,ann}}
\]

- **Interpretation:** Return relative to downside risk only.
- **Edge cases:** `None` if fewer than two downside observations or zero downside dev.
- **Code:** `sortino_ratio()`; `sortino_target_periodic` stored in metrics dict (0.0).

---

## Beta (CAPM, sample)

\[
\beta = \frac{\widehat{\text{Cov}}(e_{p}, e_{b})}{\widehat{\text{Var}}(e_{b})}
\]

with \(e_p = r_p - r_f\), \(e_b = r_b - r_f\).

- **Interpretation:** Sample sensitivity of portfolio excess to benchmark excess.
- **Edge cases:** `None` if \(\widehat{\text{Var}}(e_b)=0\) or \(n<2\).
- **Code:** `beta()` — same excess definition as CAPM regression slope **in population**; OLS \(\hat\beta\) may differ slightly due to regression intercept.

---

## Tracking error and information ratio

**Tracking error:**

\[
TE = \text{std}(a_t; \text{ddof=1}) \times \sqrt{P}
\]

**Information ratio:**

\[
IR = \frac{\bar{a} \times P}{TE}
\]

- **Edge cases:** IR `None` if \(TE=0\) or undefined.
- **Code:** `tracking_error()`, `information_ratio()`

---

## Maximum drawdown

Wealth \(W_t\) from cumulative product. Running peak \(\Pi_t = \max_{s \le t} W_s\). Drawdown \(D_t = W_t/\Pi_t - 1\).

\[
\text{MDD} = \min_t D_t
\]

- **Interpretation:** Worst peak-to-trough loss; **initial** \(W_0=1\) is a peak.
- **Code:** `max_drawdown()`, `drawdown_series()`

---

## Historical Value at Risk (VaR)

For confidence \(\gamma\) (e.g. 0.95), quantile level \(q = 1-\gamma\). Empirical quantile \(r_q = Q_q(r)\).

- **UI convention (`as_positive_loss=True`):** report \(\max(-r_q, 0)\) as a **positive loss magnitude**.
- **Assumptions:** Empirical (non-parametric); no GARCH or parametric fit.
- **Edge cases:** `None` if \(n<2\).
- **Code:** `historical_var()`

---

## Expected shortfall (CVaR / ES)

Let \(r_q\) be the VaR return threshold. Tail: \(\{r_t : r_t \le r_q\}\). ES is the mean of the tail; UI uses positive loss magnitude like VaR.

- **Interpretation:** Average loss in the worst \((1-\gamma)\) fraction of days (empirical).
- **Code:** `expected_shortfall()`

---

## Rolling beta, volatility, and Sharpe

For window size \(w\), at index \(i \ge w-1\), use observations \(t \in [i-w+1, i]\) only.

- **Rolling beta:** sample CAPM beta on excess returns in window — `rolling_beta()`; NaN before full window.
- **Rolling vol:** sample std of **raw** returns in window \(\times \sqrt{P}\) — `rolling_volatility()`.
- **Rolling Sharpe:** mean excess in window \(\times P\) divided by annualized std of **excess** in window — `rolling_sharpe()`.

**No look-ahead:** first valid index is \(i = w-1\).

---

## Data validation (inputs)

See `quantlens/data.py`: required columns `date`, `portfolio_return`, `benchmark_return`; optional `risk_free_rate`; duplicate dates rejected; returns must be \(> -1\); missing returns dropped with report.

---

## Related documents

- [Statistical inference (CAPM)](statistical-inference.md)
- [QQQ vs SPY case study](case-study-qqq-spy.md)
- [Testing and reproducibility](testing.md)
