"""CAPM regression tests on deterministic data."""

import numpy as np
import pandas as pd
import pytest

from quantlens.data import AlignedReturns, ValidationReport
from quantlens.regression import run_capm_regression


def _make_capm_data(n: int = 100, alpha: float = 0.0002, beta: float = 1.2):
    np.random.seed(123)
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    rf = np.full(n, 0.0001)
    bench = np.random.normal(0.0005, 0.01, n)
    port = rf + alpha + beta * (bench - rf) + np.random.normal(0, 0.002, n)
    return AlignedReturns(
        dates=dates,
        portfolio_return=pd.Series(port),
        benchmark_return=pd.Series(bench),
        risk_free_periodic=pd.Series(rf),
        report=ValidationReport(n_rows_aligned=n),
    )


def test_regression_alpha_beta():
    # Noise-free excess-return CAPM for exact coefficient recovery.
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
    res = run_capm_regression(data, periods_per_year=252, hac_lags=2)
    assert res is not None
    assert res.periodic_beta == pytest.approx(beta, abs=1e-6)
    assert res.periodic_alpha == pytest.approx(alpha, abs=1e-6)
    assert res.r_squared == pytest.approx(1.0, abs=1e-9)


def test_regression_noisy_beta():
    data = _make_capm_data(n=200, alpha=0.0002, beta=1.2)
    res = run_capm_regression(data, periods_per_year=252, hac_lags=3)
    assert res is not None
    assert res.periodic_beta == pytest.approx(1.2, rel=0.15)
    assert len(res.inference) == 2
    assert res.inference[1].std_err_hac > 0


def test_constant_benchmark_returns_none():
    n = 50
    dates = pd.date_range("2020-01-01", periods=n, freq="B")
    data = AlignedReturns(
        dates=dates,
        portfolio_return=pd.Series(np.random.randn(n) * 0.01),
        benchmark_return=pd.Series(np.zeros(n)),
        risk_free_periodic=pd.Series(np.zeros(n)),
        report=ValidationReport(n_rows_aligned=n),
    )
    assert run_capm_regression(data) is None
