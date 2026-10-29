"""Tests for CSV validation and alignment."""

import pytest

from quantlens.data import (
    DataValidationError,
    annual_to_periodic_rate,
    validate_and_align,
)


def test_annual_to_periodic():
    assert annual_to_periodic_rate(0.04, 252) == pytest.approx(0.04 / 252)


def test_valid_minimal_csv():
    csv = "date,portfolio_return,benchmark_return\n2020-01-02,0.01,0.005\n2020-01-03,-0.002,0.001\n"
    data = validate_and_align(csv, annual_risk_free_rate=0.0, periods_per_year=252)
    assert len(data.portfolio_return) == 2
    assert data.dates[0] < data.dates[1]


def test_missing_column():
    csv = "date,portfolio_return\n2020-01-02,0.01\n"
    with pytest.raises(DataValidationError, match="Missing required"):
        validate_and_align(csv)


def test_duplicate_dates():
    csv = (
        "date,portfolio_return,benchmark_return\n"
        "2020-01-02,0.01,0.005\n"
        "2020-01-02,0.02,0.006\n"
    )
    with pytest.raises(DataValidationError, match="Duplicate"):
        validate_and_align(csv)


def test_impossible_return():
    csv = "date,portfolio_return,benchmark_return\n2020-01-02,-1.0,0.01\n"
    with pytest.raises(DataValidationError, match="greater than -100%"):
        validate_and_align(csv)


def test_missing_values_dropped():
    csv = (
        "date,portfolio_return,benchmark_return\n"
        "2020-01-02,0.01,0.005\n"
        "2020-01-03,,0.001\n"
        "2020-01-06,0.002,0.003\n"
    )
    data = validate_and_align(csv)
    assert len(data.portfolio_return) == 2
    assert data.report.dropped_rows


def test_empty_file():
    with pytest.raises(DataValidationError, match="empty"):
        validate_and_align("date,portfolio_return,benchmark_return\n")


def test_short_sample():
    csv = "date,portfolio_return,benchmark_return\n2020-01-02,0.01,0.005\n"
    with pytest.raises(DataValidationError, match="at least"):
        validate_and_align(csv, min_observations=2)
