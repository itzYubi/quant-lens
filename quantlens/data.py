"""CSV parsing, validation, and return alignment."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from typing import BinaryIO, TextIO, Union

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("date", "portfolio_return", "benchmark_return")
OPTIONAL_COLUMNS = ("risk_free_rate",)


@dataclass
class ValidationReport:
    """Summary of parsing and alignment steps."""

    n_rows_raw: int = 0
    n_rows_aligned: int = 0
    dropped_rows: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AlignedReturns:
    """Aligned portfolio and benchmark return series."""

    dates: pd.DatetimeIndex
    portfolio_return: pd.Series
    benchmark_return: pd.Series
    risk_free_periodic: pd.Series | None
    report: ValidationReport


class DataValidationError(ValueError):
    """Raised when CSV data fails validation."""


def annual_to_periodic_rate(annual_rate: float, periods_per_year: int) -> float:
    """
    Convert an annual simple risk-free rate to an equivalent per-period rate.

    Convention: periodic_rf = annual_rf / periods_per_year (simple scaling).
    """
    return annual_rate / periods_per_year


def _read_dataframe(source: Union[str, TextIO, BinaryIO, bytes]) -> pd.DataFrame:
    if isinstance(source, bytes):
        source = source.decode("utf-8")
    if isinstance(source, str):
        if "\n" in source or source.strip().endswith(".csv"):
            try:
                return pd.read_csv(StringIO(source) if "\n" in source else source)
            except Exception as exc:
                raise DataValidationError(f"Malformed CSV: {exc}") from exc
        return pd.read_csv(source)
    return pd.read_csv(source)


def validate_and_align(
    source: Union[str, TextIO, BinaryIO, bytes],
    *,
    annual_risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    risk_free_column_is_annual: bool = False,
    min_observations: int = 2,
) -> AlignedReturns:
    """
    Parse CSV, validate columns and values, sort by date, and align series.

    Per-row ``risk_free_rate`` is treated as **per-period** decimal return unless
    ``risk_free_column_is_annual`` is True (then divided by periods_per_year).
    UI-supplied annual rate is converted with ``annual_to_periodic_rate``.
    """
    report = ValidationReport()
    try:
        df = _read_dataframe(source)
    except DataValidationError:
        raise
    except Exception as exc:
        raise DataValidationError(f"Could not read CSV: {exc}") from exc

    if df.empty:
        raise DataValidationError("CSV file is empty.")

    report.n_rows_raw = len(df)
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected: {', '.join(REQUIRED_COLUMNS)}."
        )

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna()
    if bad_dates.any():
        n_bad = int(bad_dates.sum())
        report.dropped_rows.append(f"{n_bad} row(s) with unparseable dates removed.")
        df = df.loc[~bad_dates]

    dup_mask = df["date"].duplicated(keep=False)
    if dup_mask.any():
        dup_dates = df.loc[dup_mask, "date"].dt.strftime("%Y-%m-%d").unique()
        raise DataValidationError(
            f"Duplicate dates found: {', '.join(dup_dates[:5])}"
            + (" ..." if len(dup_dates) > 5 else "")
        )

    for col in ("portfolio_return", "benchmark_return"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "risk_free_rate" in df.columns:
        df["risk_free_rate"] = pd.to_numeric(df["risk_free_rate"], errors="coerce")

    missing_ret = df["portfolio_return"].isna() | df["benchmark_return"].isna()
    if missing_ret.any():
        n = int(missing_ret.sum())
        report.dropped_rows.append(f"{n} row(s) with missing return values removed.")
        df = df.loc[~missing_ret]

    for col in ("portfolio_return", "benchmark_return"):
        impossible = df[col] <= -1.0
        if impossible.any():
            raise DataValidationError(
                f"Simple returns in '{col}' must be greater than -100% (> -1)."
            )

    df = df.sort_values("date").reset_index(drop=True)

    if "risk_free_rate" in df.columns:
        rf = df["risk_free_rate"].copy()
        if risk_free_column_is_annual:
            rf = rf / periods_per_year
        if rf.isna().any():
            n = int(rf.isna().sum())
            report.warnings.append(
                f"{n} missing risk_free_rate value(s); using UI annual rate for those rows."
            )
            rf = rf.fillna(annual_to_periodic_rate(annual_risk_free_rate, periods_per_year))
        risk_free_periodic = rf
    else:
        periodic_ui = annual_to_periodic_rate(annual_risk_free_rate, periods_per_year)
        risk_free_periodic = pd.Series(periodic_ui, index=df.index)

    report.n_rows_aligned = len(df)
    if report.n_rows_aligned < min_observations:
        raise DataValidationError(
            f"Need at least {min_observations} aligned observations; "
            f"got {report.n_rows_aligned}."
        )

    dates = pd.DatetimeIndex(df["date"])
    return AlignedReturns(
        dates=dates,
        portfolio_return=df["portfolio_return"].reset_index(drop=True),
        benchmark_return=df["benchmark_return"].reset_index(drop=True),
        risk_free_periodic=risk_free_periodic.reset_index(drop=True),
        report=report,
    )


def aligned_to_frame(data: AlignedReturns) -> pd.DataFrame:
    """Return a single DataFrame for analysis and export."""
    out = pd.DataFrame(
        {
            "date": data.dates,
            "portfolio_return": data.portfolio_return,
            "benchmark_return": data.benchmark_return,
        }
    )
    if data.risk_free_periodic is not None:
        out["risk_free_rate"] = data.risk_free_periodic
    return out
