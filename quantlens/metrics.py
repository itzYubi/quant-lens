"""Performance and risk metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from quantlens.data import AlignedReturns


@dataclass
class MetricResult:
    name: str
    value: float | None
    unit: str
    definition: str


def cumulative_wealth(returns: pd.Series) -> pd.Series:
    """Wealth index starting at 1: cumprod(1 + r)."""
    return (1.0 + returns).cumprod()


def cumulative_growth_final(returns: pd.Series) -> float:
    """Ending wealth index (starts at 1)."""
    if len(returns) == 0:
        return np.nan
    return float((1.0 + returns).prod())


def cagr(returns: pd.Series, periods_per_year: int) -> float | None:
    """
    CAGR from simple returns: (W_T / W_0)^(periods_per_year / n) - 1 with W_0 = 1.
    """
    n = len(returns)
    if n < 1:
        return None
    ending = cumulative_growth_final(returns)
    if ending <= 0:
        return None
    return float(ending ** (periods_per_year / n) - 1.0)


def annualized_arithmetic_return(returns: pd.Series, periods_per_year: int) -> float:
    """Mean periodic return × periods_per_year."""
    return float(returns.mean() * periods_per_year)


def annualized_volatility(returns: pd.Series, periods_per_year: int) -> float | None:
    """Sample std (ddof=1) × sqrt(periods_per_year). None if n < 2."""
    if len(returns) < 2:
        return None
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def excess_returns(returns: pd.Series, rf_periodic: pd.Series) -> pd.Series:
    return returns - rf_periodic


def sharpe_ratio(
    returns: pd.Series,
    rf_periodic: pd.Series,
    periods_per_year: int,
) -> float | None:
    """Annualized mean excess return / annualized excess-return volatility (ddof=1)."""
    ex = excess_returns(returns, rf_periodic)
    vol = annualized_volatility(ex, periods_per_year)
    if vol is None or vol == 0:
        return None
    ann_ex = float(ex.mean() * periods_per_year)
    return ann_ex / vol


def sortino_ratio(
    returns: pd.Series,
    rf_periodic: pd.Series,
    periods_per_year: int,
    target_periodic: float | None = None,
) -> float | None:
    """
    Sortino: annualized mean excess return / annualized downside deviation.

    Minimum acceptable return ``target_periodic`` applies to **simple returns**;
    downside deviations use excess returns below ``target_periodic - rf_periodic``.
    """
    if target_periodic is None:
        target_periodic = 0.0
    ex = excess_returns(returns, rf_periodic)
    ann_ex = float(ex.mean() * periods_per_year)
    ex_mar = target_periodic - rf_periodic
    shortfall = ex - ex_mar
    downside = shortfall[shortfall < 0]
    if len(downside) < 2:
        return None
    down_dev = float(downside.std(ddof=1) * np.sqrt(periods_per_year))
    if down_dev == 0:
        return None
    return ann_ex / down_dev


def beta(
    portfolio: pd.Series,
    benchmark: pd.Series,
    rf_periodic: pd.Series,
) -> float | None:
    """Cov(p-bench excess, bench excess) / Var(bench excess); rf=0 if not supplied."""
    p_ex = portfolio - rf_periodic
    b_ex = benchmark - rf_periodic
    if len(b_ex) < 2:
        return None
    var_b = b_ex.var(ddof=1)
    if var_b == 0:
        return None
    return float(p_ex.cov(b_ex) / var_b)


def active_returns(portfolio: pd.Series, benchmark: pd.Series) -> pd.Series:
    return portfolio - benchmark


def tracking_error(
    portfolio: pd.Series,
    benchmark: pd.Series,
    periods_per_year: int,
) -> float | None:
    act = active_returns(portfolio, benchmark)
    if len(act) < 2:
        return None
    return float(act.std(ddof=1) * np.sqrt(periods_per_year))


def information_ratio(
    portfolio: pd.Series,
    benchmark: pd.Series,
    periods_per_year: int,
) -> float | None:
    act = active_returns(portfolio, benchmark)
    te = tracking_error(portfolio, benchmark, periods_per_year)
    if te is None or te == 0:
        return None
    ann_active = float(act.mean() * periods_per_year)
    return ann_active / te


def drawdown_series(wealth: pd.Series) -> pd.Series:
    """Drawdown = wealth / running_max(wealth) - 1; initial wealth is a peak."""
    peak = wealth.cummax()
    return wealth / peak - 1.0


def max_drawdown(returns: pd.Series) -> float:
    """Minimum drawdown (negative number)."""
    wealth = cumulative_wealth(returns)
    return float(drawdown_series(wealth).min())


def historical_var(
    returns: pd.Series,
    confidence: float,
    *,
    as_positive_loss: bool = True,
) -> float | None:
    """
    Historical VaR at ``confidence`` (e.g. 0.95).

    ``as_positive_loss=True``: report the magnitude of loss as a positive number
    (e.g. 2% loss → 0.02). Otherwise return the negative return quantile.
    """
    if len(returns) < 2:
        return None
    q = 1.0 - confidence
    var_return = float(np.quantile(returns, q))
    if as_positive_loss:
        return float(max(-var_return, 0.0))
    return var_return


def expected_shortfall(
    returns: pd.Series,
    confidence: float,
    *,
    as_positive_loss: bool = True,
) -> float | None:
    """
    Expected shortfall (CVaR): mean of returns at or below the VaR return threshold.
    """
    if len(returns) < 2:
        return None
    q = 1.0 - confidence
    var_return = float(np.quantile(returns, q))
    tail = returns[returns <= var_return]
    if len(tail) == 0:
        return None
    es = float(tail.mean())
    if as_positive_loss:
        return float(max(-es, 0.0))
    return es


def rolling_beta(
    portfolio: pd.Series,
    benchmark: pd.Series,
    rf_periodic: pd.Series,
    window: int,
) -> pd.Series:
    """Rolling CAPM beta; NaN until a full window is available."""
    p_ex = (portfolio - rf_periodic).values
    b_ex = (benchmark - rf_periodic).values
    n = len(portfolio)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        sl = slice(i - window + 1, i + 1)
        bx = b_ex[sl]
        px = p_ex[sl]
        var_b = np.var(bx, ddof=1)
        if var_b > 0:
            out[i] = np.cov(px, bx, ddof=1)[0, 1] / var_b
    return pd.Series(out, index=portfolio.index)


def rolling_volatility(
    returns: pd.Series,
    window: int,
    periods_per_year: int,
) -> pd.Series:
    """Rolling annualized volatility; NaN until window full."""
    roll = returns.rolling(window=window, min_periods=window)
    return roll.std(ddof=1) * np.sqrt(periods_per_year)


def rolling_sharpe(
    returns: pd.Series,
    rf_periodic: pd.Series,
    window: int,
    periods_per_year: int,
) -> pd.Series:
    """Rolling annualized Sharpe; NaN until window full."""
    ex = returns - rf_periodic
    roll_ex = ex.rolling(window=window, min_periods=window).mean() * periods_per_year
    roll_vol = rolling_volatility(ex, window, periods_per_year)
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = roll_ex / roll_vol
    sharpe = sharpe.where(roll_vol > 0)
    return sharpe


def compute_all_metrics(
    data: AlignedReturns,
    *,
    periods_per_year: int = 252,
    var_confidence: float = 0.95,
) -> dict[str, Any]:
    """Compute standard metric bundle for portfolio and benchmark."""
    p = data.portfolio_return
    b = data.benchmark_return
    rf = data.risk_free_periodic
    assert rf is not None

    metrics: dict[str, Any] = {
        "n_observations": len(p),
        "portfolio_cagr": cagr(p, periods_per_year),
        "portfolio_ann_arith_return": annualized_arithmetic_return(p, periods_per_year),
        "portfolio_ann_vol": annualized_volatility(p, periods_per_year),
        "portfolio_sharpe": sharpe_ratio(p, rf, periods_per_year),
        "portfolio_sortino": sortino_ratio(p, rf, periods_per_year),
        "portfolio_max_drawdown": max_drawdown(p),
        "portfolio_var": historical_var(p, var_confidence),
        "portfolio_es": expected_shortfall(p, var_confidence),
        "benchmark_cagr": cagr(b, periods_per_year),
        "benchmark_ann_arith_return": annualized_arithmetic_return(b, periods_per_year),
        "benchmark_ann_vol": annualized_volatility(b, periods_per_year),
        "beta": beta(p, b, rf),
        "tracking_error": tracking_error(p, b, periods_per_year),
        "information_ratio": information_ratio(p, b, periods_per_year),
        "var_confidence": var_confidence,
        "var_convention": "positive_loss_magnitude",
        "periods_per_year": periods_per_year,
        "sortino_target_periodic": 0.0,
    }
    return metrics


METRIC_DEFINITIONS: dict[str, tuple[str, str, str]] = {
    "n_observations": ("Observations", "count", "Number of aligned return observations"),
    "portfolio_cagr": ("Portfolio CAGR", "annual rate", "Compound annual growth from simple returns"),
    "portfolio_ann_arith_return": (
        "Portfolio ann. arithmetic return",
        "annual rate",
        "Mean periodic return × periods/year (not CAGR)",
    ),
    "portfolio_ann_vol": (
        "Portfolio ann. volatility",
        "annualized stdev",
        "Sample std of portfolio returns (ddof=1) × √periods/year",
    ),
    "portfolio_sharpe": (
        "Portfolio Sharpe",
        "ratio",
        "Ann. mean excess / ann. excess-return vol",
    ),
    "portfolio_sortino": (
        "Portfolio Sortino",
        "ratio",
        "Ann. mean excess / ann. downside dev of excess below (MAR − RF); MAR=0 per period",
    ),
    "portfolio_max_drawdown": (
        "Portfolio max drawdown",
        "fraction",
        "Min wealth/peak − 1 (initial wealth=1 is a peak)",
    ),
    "portfolio_var": (
        "Portfolio VaR (loss)",
        "fraction",
        "Historical VaR as positive loss at stated confidence",
    ),
    "portfolio_es": (
        "Portfolio expected shortfall",
        "fraction",
        "Tail mean at or below VaR threshold; positive loss convention",
    ),
    "benchmark_cagr": ("Benchmark CAGR", "annual rate", "Benchmark compound annual growth"),
    "benchmark_ann_arith_return": (
        "Benchmark ann. arithmetic return",
        "annual rate",
        "Benchmark mean periodic return × periods/year",
    ),
    "benchmark_ann_vol": (
        "Benchmark ann. volatility",
        "annualized stdev",
        "Benchmark return sample std × √periods/year",
    ),
    "beta": ("Beta (CAPM)", "ratio", "Cov(portfolio ex., benchmark ex.) / Var(benchmark ex.)"),
    "tracking_error": (
        "Tracking error",
        "annualized stdev",
        "Std of active returns × √periods/year",
    ),
    "information_ratio": (
        "Information ratio",
        "ratio",
        "Ann. mean active return / tracking error",
    ),
}


def format_metric_display(key: str, val: float | int | None, unit: str) -> str:
    """Format a metric for the UI."""
    if val is None or val == "":
        return "N/A"
    if key == "n_observations":
        return str(int(val))
    if unit == "ratio":
        return f"{float(val):.4f}"
    if unit in ("annual rate", "fraction", "annualized stdev"):
        return f"{float(val):.2%}"
    return f"{float(val):.6f}"


def metrics_table_rows(metrics: dict[str, Any]) -> list[dict[str, str]]:
    """Human-readable rows for UI / CSV export."""
    rows = []
    ppy = metrics.get("periods_per_year", 252)
    conf = metrics.get("var_confidence")
    for key, (label, unit, definition) in METRIC_DEFINITIONS.items():
        val = metrics.get(key)
        row = {
            "metric_key": key,
            "metric": label,
            "value_raw": "" if val is None else val,
            "display_value": format_metric_display(key, val, unit),
            "unit": unit,
            "definition": definition,
        }
        rows.append(row)
    if conf is not None:
        rows.append(
            {
                "metric_key": "var_confidence",
                "metric": "VaR / ES confidence",
                "value_raw": conf,
                "display_value": f"{float(conf):.0%}",
                "unit": "probability",
                "definition": "Quantile level for historical VaR and ES",
            }
        )
    rows.append(
        {
            "metric_key": "periods_per_year",
            "metric": "Periods per year",
            "value_raw": ppy,
            "display_value": str(int(ppy)),
            "unit": "convention",
            "definition": "Annualization factor for rates and volatilities",
        }
    )
    return rows
