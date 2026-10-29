"""End-to-end checks: sample load, exports match metrics, validation errors."""

import json
from pathlib import Path

import pytest

from quantlens.data import DataValidationError, validate_and_align
from quantlens.metrics import compute_all_metrics, metrics_table_rows
from quantlens.regression import regression_to_dict, run_capm_regression
from quantlens.report import build_research_summary

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample_returns.csv"


def test_sample_csv_loads():
    data = validate_and_align(SAMPLE.read_bytes(), annual_risk_free_rate=0.04)
    assert data.report.n_rows_aligned >= 60
    assert data.dates.is_monotonic_increasing


def test_metrics_json_export_matches_computed():
    data = validate_and_align(SAMPLE.read_bytes(), annual_risk_free_rate=0.04)
    metrics = compute_all_metrics(data, periods_per_year=252, var_confidence=0.95)
    reg = run_capm_regression(data, periods_per_year=252)
    payload = {
        "metrics": {k: v for k, v in metrics.items() if k != "var_convention"},
        "regression": regression_to_dict(reg) if reg else None,
    }
    raw = json.loads(json.dumps(payload, default=str))
    assert raw["metrics"]["n_observations"] == metrics["n_observations"]
    assert raw["metrics"]["portfolio_cagr"] == metrics["portfolio_cagr"]
    if reg:
        assert raw["regression"]["periodic_beta"] == reg.periodic_beta


def test_research_summary_uses_regression_pvalues():
    data = validate_and_align(SAMPLE.read_bytes())
    metrics = compute_all_metrics(data)
    reg = run_capm_regression(data)
    lines = build_research_summary(metrics, reg, None, metrics["n_observations"])
    text = " ".join(lines)
    if reg:
        assert f"{reg.inference[0].p_value_ols:.4f}" in text
        assert f"{reg.inference[0].p_value_hac:.4f}" in text
    assert "significant" not in text.lower() or "not proof" in text.lower()


def test_malformed_and_duplicate_csv():
    with pytest.raises(DataValidationError):
        validate_and_align("not,a,valid\n1,2")
    dup = (
        "date,portfolio_return,benchmark_return\n"
        "2020-01-02,0.01,0.02\n"
        "2020-01-02,0.02,0.03\n"
    )
    with pytest.raises(DataValidationError, match="Duplicate"):
        validate_and_align(dup)


def test_valid_upload_like_csv():
    csv = (
        "date,portfolio_return,benchmark_return\n"
        + "\n".join(
            f"2020-01-{2+i:02d},{0.001*i},{0.0005*i}" for i in range(10)
        )
        + "\n"
    )
    data = validate_and_align(csv, min_observations=5)
    assert len(data.portfolio_return) == 10
