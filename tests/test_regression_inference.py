"""Regression inference and diagnostics tests."""

import numpy as np
import pandas as pd
import pytest

from quantlens.data import AlignedReturns, ValidationReport
from quantlens.regression import default_hac_lags, run_capm_regression


def test_default_hac_lags():
    assert default_hac_lags(100) == int(np.floor(4 * (100 / 100.0) ** (2.0 / 9.0)))


def test_ols_hac_same_coefficients_different_se():
    n = 80
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    rf_s = pd.Series([0.0001] * n)
    bench = pd.Series(np.linspace(-0.02, 0.03, n))
    alpha = 0.0003
    beta = 0.9
    port = rf_s + alpha + beta * (bench - rf_s)
    data = AlignedReturns(
        dates=dates,
        portfolio_return=port,
        benchmark_return=bench,
        risk_free_periodic=rf_s,
        report=ValidationReport(n_rows_aligned=n),
    )
    res = run_capm_regression(data, periods_per_year=252, hac_lags=2, confidence=0.95)
    assert res is not None
    alpha_row = res.inference[0]
    beta_row = res.inference[1]
    assert alpha_row.estimate == pytest.approx(alpha, abs=1e-6)
    assert beta_row.estimate == pytest.approx(beta, abs=1e-6)
    assert alpha_row.ci_low_ols <= alpha_row.estimate <= alpha_row.ci_high_ols
    assert beta_row.ci_low_ols <= beta_row.estimate <= beta_row.ci_high_ols
    assert res.diagnostics.f_statistic > 0
    assert 0 <= res.diagnostics.durbin_watson <= 4


def test_regression_export_includes_diagnostics():
    n = 40
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    bench = pd.Series(np.random.default_rng(1).normal(0, 0.01, n))
    rf = pd.Series([0.0001] * n)
    port = rf + 0.0002 + 1.1 * (bench - rf)
    data = AlignedReturns(
        dates=dates,
        portfolio_return=pd.Series(port),
        benchmark_return=bench,
        risk_free_periodic=rf,
        report=ValidationReport(n_rows_aligned=n),
    )
    from quantlens.regression import regression_to_dict

    payload = regression_to_dict(run_capm_regression(data))
    assert "diagnostics" in payload
    assert "f_statistic" in payload["diagnostics"]
