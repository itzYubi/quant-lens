"""Verify OLS vs HAC coefficient identity."""

import numpy as np
import pandas as pd
import pytest

from quantlens.data import AlignedReturns, ValidationReport
from quantlens.regression import default_hac_lags, run_capm_regression


def test_hac_lag_documented_rule():
    n = 300
    assert default_hac_lags(n) == int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0)))


def test_ols_hac_estimates_identical():
    rng = np.random.default_rng(99)
    n = 120
    dates = pd.date_range("2021-01-01", periods=n, freq="B")
    rf = pd.Series([0.0002] * n)
    bench = pd.Series(rng.normal(0.0004, 0.012, n))
    port = rf + 0.00015 + 1.05 * (bench - rf) + rng.normal(0, 0.003, n)
    data = AlignedReturns(
        dates=dates,
        portfolio_return=port,
        benchmark_return=bench,
        risk_free_periodic=rf,
        report=ValidationReport(n_rows_aligned=n),
    )
    res = run_capm_regression(data, hac_lags=default_hac_lags(n))
    assert res is not None
    alpha_row, beta_row = res.inference
    assert alpha_row.estimate == pytest.approx(res.periodic_alpha)
    assert beta_row.estimate == pytest.approx(res.periodic_beta)
    assert alpha_row.std_err_hac >= 0
    assert alpha_row.std_err_ols >= 0
