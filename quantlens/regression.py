"""CAPM OLS regression with OLS and Newey–West (HAC) inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

from quantlens.data import AlignedReturns


@dataclass
class InferenceRow:
    coefficient: str
    estimate: float
    std_err_ols: float
    p_value_ols: float
    ci_low_ols: float
    ci_high_ols: float
    std_err_hac: float
    p_value_hac: float
    ci_low_hac: float
    ci_high_hac: float


@dataclass
class RegressionDiagnostics:
    """OLS model diagnostics (coefficients unchanged under HAC)."""

    f_statistic: float
    f_pvalue: float
    durbin_watson: float
    hac_max_lags: int
    hac_lag_rule: str
    confidence_level: float


@dataclass
class CapmRegressionResult:
    n_obs: int
    r_squared: float
    adj_r_squared: float
    periodic_alpha: float
    periodic_beta: float
    annualized_alpha: float
    periods_per_year: int
    hac_lags: int
    inference: list[InferenceRow]
    diagnostics: RegressionDiagnostics
    ols_summary_text: str


def default_hac_lags(n: int) -> int:
    """Newey–West lag: floor(4 * (n/100)^(2/9)) per common rule of thumb."""
    if n < 2:
        return 0
    return int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0)))


def run_capm_regression(
    data: AlignedReturns,
    *,
    periods_per_year: int = 252,
    hac_lags: int | None = None,
    confidence: float = 0.95,
) -> CapmRegressionResult | None:
    """
    Regress portfolio excess returns on benchmark excess returns (CAPM).

    Returns None if fewer than 3 observations or benchmark excess has zero variance.
    """
    p = data.portfolio_return
    b = data.benchmark_return
    rf = data.risk_free_periodic
    assert rf is not None

    y = (p - rf).values
    x = (b - rf).values
    n = len(y)
    if n < 3:
        return None
    if np.var(x, ddof=1) == 0:
        return None

    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    lags = default_hac_lags(n) if hac_lags is None else hac_lags
    hac = model.get_robustcov_results(cov_type="HAC", maxlags=lags)

    alpha = float(model.params[0])
    beta = float(model.params[1])
    alpha_ann = alpha * periods_per_year

    rows: list[InferenceRow] = []
    names = ["alpha (intercept)", "beta (benchmark)"]
    for i, name in enumerate(names):
        est = float(model.params[i])
        se_ols = float(model.bse[i])
        p_ols = float(model.pvalues[i])
        ci_ols = model.conf_int(alpha=1 - confidence)[i]
        se_h = float(hac.bse[i])
        p_h = float(hac.pvalues[i])
        ci_h = hac.conf_int(alpha=1 - confidence)[i]
        rows.append(
            InferenceRow(
                coefficient=name,
                estimate=est,
                std_err_ols=se_ols,
                p_value_ols=p_ols,
                ci_low_ols=float(ci_ols[0]),
                ci_high_ols=float(ci_ols[1]),
                std_err_hac=se_h,
                p_value_hac=p_h,
                ci_low_hac=float(ci_h[0]),
                ci_high_hac=float(ci_h[1]),
            )
        )

    diagnostics = RegressionDiagnostics(
        f_statistic=float(model.fvalue),
        f_pvalue=float(model.f_pvalue),
        durbin_watson=float(durbin_watson(model.resid)),
        hac_max_lags=lags,
        hac_lag_rule="floor(4 * (n/100)^(2/9))",
        confidence_level=confidence,
    )

    return CapmRegressionResult(
        n_obs=n,
        r_squared=float(model.rsquared),
        adj_r_squared=float(model.rsquared_adj),
        periodic_alpha=alpha,
        periodic_beta=beta,
        annualized_alpha=alpha_ann,
        periods_per_year=periods_per_year,
        hac_lags=lags,
        inference=rows,
        diagnostics=diagnostics,
        ols_summary_text=str(model.summary()),
    )


def regression_to_dict(result: CapmRegressionResult) -> dict[str, Any]:
    """Serialize for JSON export."""
    return {
        "n_obs": result.n_obs,
        "r_squared": result.r_squared,
        "adj_r_squared": result.adj_r_squared,
        "periodic_alpha": result.periodic_alpha,
        "periodic_beta": result.periodic_beta,
        "annualized_alpha": result.annualized_alpha,
        "periods_per_year": result.periods_per_year,
        "hac_lags": result.hac_lags,
        "diagnostics": {
            "f_statistic": result.diagnostics.f_statistic,
            "f_pvalue": result.diagnostics.f_pvalue,
            "durbin_watson": result.diagnostics.durbin_watson,
            "hac_lag_rule": result.diagnostics.hac_lag_rule,
            "confidence_level": result.diagnostics.confidence_level,
        },
        "inference": [
            {
                "coefficient": r.coefficient,
                "estimate": r.estimate,
                "ols": {
                    "std_err": r.std_err_ols,
                    "p_value": r.p_value_ols,
                    "ci_low": r.ci_low_ols,
                    "ci_high": r.ci_high_ols,
                },
                "hac": {
                    "std_err": r.std_err_hac,
                    "p_value": r.p_value_hac,
                    "ci_low": r.ci_low_hac,
                    "ci_high": r.ci_high_hac,
                },
            }
            for r in result.inference
        ],
    }


def run_capm_on_slice(
    portfolio: pd.Series,
    benchmark: pd.Series,
    rf: pd.Series,
    *,
    periods_per_year: int,
    hac_lags: int | None = None,
) -> CapmRegressionResult | None:
    """CAPM on aligned series without full AlignedReturns wrapper."""
    from quantlens.data import AlignedReturns, ValidationReport

    dates = pd.date_range("2000-01-01", periods=len(portfolio), freq="D")
    data = AlignedReturns(
        dates=dates,
        portfolio_return=portfolio.reset_index(drop=True),
        benchmark_return=benchmark.reset_index(drop=True),
        risk_free_periodic=rf.reset_index(drop=True),
        report=ValidationReport(n_rows_aligned=len(portfolio)),
    )
    return run_capm_regression(data, periods_per_year=periods_per_year, hac_lags=hac_lags)
