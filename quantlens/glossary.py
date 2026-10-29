"""Plain-language definitions for QuantLens UI and regression output."""

from __future__ import annotations

GLOSSARY_SECTIONS: dict[str, list[tuple[str, str]]] = {
    "Returns and wealth": [
        (
            "Simple return",
            "Periodic return as a decimal fraction of wealth (0.01 = +1%). QuantLens compounds with "
            "wealth factor (1 + r) each period.",
        ),
        (
            "Cumulative wealth / growth",
            "Wealth index starting at 1: product of (1 + r_t). Ending value shows total growth over the sample.",
        ),
        (
            "CAGR",
            "Compound annual growth rate: annualized constant rate that would compound to the same ending "
            "wealth over n periods. Distinct from mean return × periods/year.",
        ),
        (
            "Annualized arithmetic return",
            "Average periodic return scaled by periods per year (e.g. 252). Describes typical period size, "
            "not compounded growth.",
        ),
        (
            "Excess return",
            "Portfolio (or benchmark) return minus the periodic risk-free rate for that date.",
        ),
        (
            "Active return",
            "Portfolio return minus benchmark return (relative performance per period).",
        ),
    ],
    "Risk and risk-adjusted metrics": [
        (
            "Annualized volatility",
            "Sample standard deviation of returns (ddof=1) × √(periods per year). Measures dispersion of "
            "periodic returns, not forecast uncertainty.",
        ),
        (
            "Sharpe ratio",
            "Annualized mean excess return divided by annualized volatility of **excess** returns. Higher "
            "values mean more return per unit of total volatility, given the chosen risk-free rate.",
        ),
        (
            "Sortino ratio",
            "Annualized mean excess return divided by annualized downside deviation. QuantLens uses MAR = 0 "
            "on simple returns; downside is based on excess returns below (MAR − RF).",
        ),
        (
            "Maximum drawdown",
            "Largest peak-to-trough decline in the wealth index (negative fraction). Initial wealth = 1 "
            "counts as a peak.",
        ),
        (
            "Beta",
            "Covariance of portfolio and benchmark **excess** returns divided by variance of benchmark "
            "excess returns. Measures benchmark sensitivity, not a separate regression from CAPM β unless "
            "definitions align.",
        ),
        (
            "Tracking error",
            "Annualized standard deviation of active returns (portfolio − benchmark).",
        ),
        (
            "Information ratio",
            "Annualized mean active return divided by tracking error.",
        ),
        (
            "Historical VaR",
            "Value at Risk from the empirical return distribution at the chosen confidence level. QuantLens "
            "reports **positive loss magnitude** (e.g. 2% daily loss shown as 0.02).",
        ),
        (
            "Expected shortfall (CVaR / ES)",
            "Average return in the tail at or below the historical VaR threshold; reported as positive loss "
            "magnitude like VaR.",
        ),
    ],
    "Rolling analysis": [
        (
            "Rolling window",
            "Number of consecutive observations used for each rolling point. QuantLens only plots a value "
            "after a **full** window is available (no look-ahead).",
        ),
        (
            "Rolling beta",
            "CAPM-style beta estimated inside each rolling window: Cov(portfolio ex., benchmark ex.) / "
            "Var(benchmark ex.) with the same risk-free convention as the main metrics.",
        ),
        (
            "Rolling volatility",
            "Annualized sample volatility inside each window (ddof=1 × √(periods/year)).",
        ),
        (
            "Rolling Sharpe",
            "Annualized mean excess return in the window divided by annualized excess-return volatility in "
            "the same window.",
        ),
    ],
    "CAPM and regression": [
        (
            "CAPM",
            "Capital Asset Pricing Model: linear model regressing portfolio **excess** returns on benchmark "
            "**excess** returns. Intercept = Jensen's alpha (periodic); slope = beta.",
        ),
        (
            "Alpha (α)",
            "Regression intercept: average portfolio excess return not explained by benchmark exposure in "
            "the CAPM line. QuantLens shows periodic α and annualized α (periodic × periods/year).",
        ),
        (
            "R-squared (R²)",
            "Fraction of variance in portfolio excess returns explained by benchmark excess returns in the "
            "OLS fit.",
        ),
        (
            "Adjusted R²",
            "R² penalized for number of regressors; useful when comparing models with different complexity.",
        ),
        (
            "OLS",
            "Ordinary least squares: standard linear regression. Conventional standard errors assume "
            "homoskedastic, uncorrelated errors.",
        ),
        (
            "HAC / Newey–West",
            "Heteroskedasticity- and autocorrelation-consistent standard errors. **Coefficients match OLS**; "
            "only uncertainty (SE, p-values, CIs) may change. Lag count follows floor(4×(n/100)^(2/9)) unless "
            "overridden.",
        ),
        (
            "Standard error",
            "Estimated sampling uncertainty for a coefficient; used with t-tests and confidence intervals.",
        ),
        (
            "p-value",
            "Probability of observing a test statistic at least as extreme as the sample's, if the null "
            "hypothesis were true. QuantLens does not equate low p-values with proof of skill.",
        ),
        (
            "Confidence interval (CI)",
            "Range of parameter values consistent with the data at the stated confidence level (default 95%) "
            "under the stated inference method (OLS or HAC).",
        ),
    ],
    "OLS summary diagnostics (full regression output)": [
        (
            "F-statistic / Prob(F-statistic)",
            "Classical **OLS** test of whether all slope coefficients are jointly zero (not HAC-robust). "
            "A small Prob(F) suggests the benchmark factor explains portfolio excess variation in the linear "
            "model.",
        ),
        (
            "Durbin–Watson",
            "Statistic near 2 suggests little first-order autocorrelation in OLS residuals; values far from "
            "2 may indicate autocorrelation, which can invalidate conventional OLS standard errors (motivating HAC).",
        ),
        (
            "Skewness",
            "Third standardized moment of regression residuals. Non-zero skew means residual distribution is "
            "asymmetric.",
        ),
        (
            "Kurtosis",
            "Fourth-moment tail heaviness of residuals (statsmodels reports excess kurtosis relative to "
            "normal). Large values indicate fat tails versus a normal distribution.",
        ),
        (
            "Jarque–Bera (JB)",
            "Test statistic combining skewness and kurtosis to assess whether residuals look normal; often "
            "shown with a p-value in the OLS summary.",
        ),
        (
            "Omnibus / Prob(Omnibus)",
            "In statsmodels OLS output, **Omnibus** refers to the Jarque–Bera normality test on residuals; "
            "**Prob(Omnibus)** is its p-value. It is descriptive on the residual distribution, not a forecast "
            "of future alpha.",
        ),
    ],
    "Regimes and research summary": [
        (
            "Descriptive regime split",
            "Observations grouped by whether benchmark return is ≥ 0 or < 0. Simple description only—not a "
            "latent regime model or forecast.",
        ),
        (
            "Subperiod sensitivity",
            "Metrics and alpha recomputed on first vs second half of the sample to show stability over time.",
        ),
        (
            "Outlier diagnostic",
            "Optional re-estimation after dropping largest |portfolio return| days; labeled diagnostic, not "
            "primary results.",
        ),
    ],
    "Data and settings": [
        (
            "Periods per year",
            "Annualization factor (default 252 trading days). Applied to means and volatilities consistently.",
        ),
        (
            "Risk-free rate",
            "Sidebar annual rate converted to periodic as annual / periods per year, unless a per-row CSV "
            "column supplies periodic or annual values (see checkbox).",
        ),
        (
            "Aligned observations",
            "Rows with valid dates and returns, sorted in time, with portfolio and benchmark on the same dates.",
        ),
    ],
}


def filter_glossary(query: str) -> dict[str, list[tuple[str, str]]]:
    """Return sections whose terms or definitions match query (case-insensitive)."""
    q = query.strip().lower()
    if not q:
        return GLOSSARY_SECTIONS
    out: dict[str, list[tuple[str, str]]] = {}
    for section, items in GLOSSARY_SECTIONS.items():
        matched = [
            (term, body)
            for term, body in items
            if q in term.lower() or q in body.lower()
        ]
        if matched:
            out[section] = matched
    return out
