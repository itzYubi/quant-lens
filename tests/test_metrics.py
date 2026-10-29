"""Tests for performance and risk metrics."""

import numpy as np
import pandas as pd
import pytest

from quantlens.metrics import (
    beta,
    cagr,
    cumulative_growth_final,
    cumulative_wealth,
    expected_shortfall,
    historical_var,
    max_drawdown,
    rolling_beta,
    sharpe_ratio,
    annualized_volatility,
)


def test_cumulative_growth_and_cagr():
    r = pd.Series([0.10, -0.05, 0.02])
    assert cumulative_growth_final(r) == pytest.approx(1.1 * 0.95 * 1.02)
    wealth = cumulative_wealth(r)
    assert wealth.iloc[-1] == pytest.approx(cumulative_growth_final(r))
    # n=3, ending wealth as above, periods_per_year=252
    ending = 1.1 * 0.95 * 1.02
    expected_cagr = ending ** (252 / 3) - 1
    assert cagr(r, 252) == pytest.approx(expected_cagr)


def test_annualized_volatility():
    r = pd.Series([0.01, -0.01, 0.02, -0.02])
    vol = annualized_volatility(r, 252)
    assert vol == pytest.approx(r.std(ddof=1) * np.sqrt(252))


def test_sharpe_zero_volatility():
    r = pd.Series([0.01] * 5)
    rf = pd.Series([0.0] * 5)
    assert sharpe_ratio(r, rf, 252) is None


def test_beta_synthetic():
    np.random.seed(0)
    n = 100
    b = pd.Series(np.random.normal(0, 0.01, n))
    rf = pd.Series(np.zeros(n))
    p = 1.5 * b + 0.001
    b_hat = beta(p, b, rf)
    assert b_hat == pytest.approx(1.5, rel=0.05)


def test_max_drawdown_includes_initial_peak():
    # Peak at start: drop from 1 to 0.9 is -10%
    r = pd.Series([0.0, -0.10])
    assert max_drawdown(r) == pytest.approx(-0.10)


def test_var_es_convention():
    r = pd.Series([-0.05, -0.02, 0.01, 0.03, -0.10, 0.02])
    var_loss = historical_var(r, 0.95, as_positive_loss=True)
    var_ret = historical_var(r, 0.95, as_positive_loss=False)
    assert var_loss >= 0
    assert var_ret <= 0
    es_loss = expected_shortfall(r, 0.95, as_positive_loss=True)
    assert es_loss >= var_loss or es_loss == pytest.approx(var_loss, abs=1e-9)


def test_rolling_beta_no_lookahead():
    n = 10
    window = 5
    b = pd.Series(np.linspace(0.001, 0.01, n))
    p = b * 2
    rf = pd.Series(np.zeros(n))
    rb = rolling_beta(p, b, rf, window)
    assert np.isnan(rb.iloc[window - 2])
    assert not np.isnan(rb.iloc[window - 1])
    # First full window: constant multiplier → beta ~ 2
    assert rb.iloc[window - 1] == pytest.approx(2.0, rel=0.01)
