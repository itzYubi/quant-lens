"""Hand-calculable and convention checks for core metrics."""

import math

import numpy as np
import pandas as pd
import pytest

from quantlens.metrics import (
    annualized_arithmetic_return,
    annualized_volatility,
    beta,
    expected_shortfall,
    historical_var,
    information_ratio,
    sharpe_ratio,
    sortino_ratio,
    tracking_error,
)


def test_annualized_arithmetic_return_hand():
    r = pd.Series([0.01, 0.02, -0.005])
    expected = r.mean() * 252
    assert annualized_arithmetic_return(r, 252) == pytest.approx(expected)


def test_tracking_error_and_information_ratio_hand():
    p = pd.Series([0.02, -0.01, 0.03, 0.0])
    b = pd.Series([0.01, -0.02, 0.025, -0.005])
    active = p - b
    te_expected = float(active.std(ddof=1) * math.sqrt(252))
    assert tracking_error(p, b, 252) == pytest.approx(te_expected)
    ir_expected = float(active.mean() * 252 / te_expected)
    assert information_ratio(p, b, 252) == pytest.approx(ir_expected)


def test_beta_exact_linear():
    b = pd.Series([0.01, 0.02, 0.03, -0.01])
    rf = pd.Series([0.0, 0.0, 0.0, 0.0])
    p = 1.25 * b
    assert beta(p, b, rf) == pytest.approx(1.25)


def test_sharpe_uses_excess_vol_with_varying_rf():
    r = pd.Series([0.03, -0.01, 0.02])
    rf = pd.Series([0.01, 0.0, 0.005])
    ex = r - rf
    ann_ex = ex.mean() * 252
    vol_ex = ex.std(ddof=1) * math.sqrt(252)
    expected = ann_ex / vol_ex
    assert sharpe_ratio(r, rf, 252) == pytest.approx(expected)


def test_sortino_hand():
    r = pd.Series([0.02, -0.03, 0.01, -0.02, 0.04])
    rf = pd.Series([0.0] * 5)
    ex = r - rf
    ann_ex = ex.mean() * 252
    shortfall = ex[ex < 0.0]
    down_dev = shortfall.std(ddof=1) * math.sqrt(252)
    assert sortino_ratio(r, rf, 252) == pytest.approx(ann_ex / down_dev)


def test_sortino_excess_mar_with_risk_free():
    r = pd.Series([0.03, -0.01, 0.02, -0.02])
    rf = pd.Series([0.01, 0.01, 0.01, 0.01])
    ex = r - rf
    mar_ex = 0.0 - rf
    shortfall = (ex - mar_ex)[(ex - mar_ex) < 0]
    ann_ex = ex.mean() * 252
    down_dev = shortfall.std(ddof=1) * math.sqrt(252)
    assert sortino_ratio(r, rf, 252, target_periodic=0.0) == pytest.approx(ann_ex / down_dev)


def test_var_es_exact_quantile():
    r = pd.Series([-0.10, -0.05, -0.02, 0.01, 0.03])
    q_ret = float(np.quantile(r, 0.05))
    assert historical_var(r, 0.95, as_positive_loss=False) == pytest.approx(q_ret)
    tail = r[r <= q_ret]
    es = float(tail.mean())
    assert expected_shortfall(r, 0.95, as_positive_loss=False) == pytest.approx(es)
