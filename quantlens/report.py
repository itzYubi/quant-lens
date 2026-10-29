"""Sensitivity checks and evidence-based research summary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from quantlens.data import AlignedReturns
from quantlens.metrics import compute_all_metrics
from quantlens.regression import run_capm_regression, run_capm_on_slice


@dataclass
class SubperiodResult:
    label: str
    start: str
    end: str
    n_obs: int
    metrics: dict[str, Any]
    alpha_annualized: float | None
    beta: float | None


@dataclass
class OutlierDiagnostic:
    n_excluded: int
    excluded_dates: list[str]
    alpha_annualized_full: float | None
    alpha_annualized_trimmed: float | None
    note: str


def split_subperiods(
    data: AlignedReturns,
    *,
    periods_per_year: int,
    var_confidence: float,
) -> list[SubperiodResult]:
    """First half vs second half when n >= 40; otherwise empty."""
    n = len(data.portfolio_return)
    if n < 40:
        return []

    mid = n // 2
    slices = [
        ("First half", 0, mid),
        ("Second half", mid, n),
    ]
    results: list[SubperiodResult] = []
    for label, start, end in slices:
        sl = slice(start, end)
        sub = AlignedReturns(
            dates=data.dates[sl],
            portfolio_return=data.portfolio_return.iloc[sl].reset_index(drop=True),
            benchmark_return=data.benchmark_return.iloc[sl].reset_index(drop=True),
            risk_free_periodic=data.risk_free_periodic.iloc[sl].reset_index(drop=True)
            if data.risk_free_periodic is not None
            else None,
            report=data.report,
        )
        m = compute_all_metrics(sub, periods_per_year=periods_per_year, var_confidence=var_confidence)
        reg = run_capm_regression(sub, periods_per_year=periods_per_year)
        alpha = reg.annualized_alpha if reg else None
        beta_v = reg.periodic_beta if reg else None
        results.append(
            SubperiodResult(
                label=label,
                start=str(sub.dates[0].date()),
                end=str(sub.dates[-1].date()),
                n_obs=len(sub.portfolio_return),
                metrics=m,
                alpha_annualized=alpha,
                beta=beta_v,
            )
        )
    return results


def outlier_alpha_diagnostic(
    data: AlignedReturns,
    *,
    periods_per_year: int,
    top_k: int = 3,
) -> OutlierDiagnostic | None:
    """
    Exclude top |portfolio return| observations as a diagnostic only.
    """
    n = len(data.portfolio_return)
    if n < 20 or top_k < 1:
        return None

    p = data.portfolio_return
    abs_p = p.abs()
    idx = abs_p.nlargest(min(top_k, n // 4)).index
    mask = ~p.index.isin(idx)
    trimmed_p = p[mask]
    trimmed_b = data.benchmark_return[mask]
    trimmed_rf = data.risk_free_periodic[mask] if data.risk_free_periodic is not None else None
    if trimmed_rf is None:
        return None

    full_reg = run_capm_regression(data, periods_per_year=periods_per_year)
    trim_reg = run_capm_on_slice(trimmed_p, trimmed_b, trimmed_rf, periods_per_year=periods_per_year)

    dates_ex = [str(data.dates[i].date()) for i in idx]
    return OutlierDiagnostic(
        n_excluded=len(idx),
        excluded_dates=dates_ex,
        alpha_annualized_full=full_reg.annualized_alpha if full_reg else None,
        alpha_annualized_trimmed=trim_reg.annualized_alpha if trim_reg else None,
        note=(
            "Diagnostic only: excludes largest |portfolio_return| observations. "
            "Primary metrics use the full sample."
        ),
    )


def build_research_summary(
    metrics: dict[str, Any],
    regression: Any | None,
    regime_warning: str | None,
    n_obs: int,
) -> list[str]:
    """
    Deterministic bullet points traceable to computed outputs.
    """
    lines: list[str] = []

    cagr = metrics.get("portfolio_cagr")
    b_cagr = metrics.get("benchmark_cagr")
    if cagr is not None and b_cagr is not None:
        lines.append(
            f"Observed portfolio CAGR ({cagr:.2%}) vs benchmark CAGR ({b_cagr:.2%}) "
            f"over {n_obs} aligned periods (descriptive, not a forecast)."
        )

    sharpe = metrics.get("portfolio_sharpe")
    vol = metrics.get("portfolio_ann_vol")
    if sharpe is not None:
        lines.append(f"Estimated annualized Sharpe ratio: {sharpe:.3f} (volatility {vol:.2%} if defined).")
    elif vol is not None and vol == 0:
        lines.append("Sharpe ratio is undefined because portfolio volatility is zero.")

    mdd = metrics.get("portfolio_max_drawdown")
    if mdd is not None:
        lines.append(f"Maximum drawdown (wealth from peak): {mdd:.2%}.")

    if regression is not None:
        alpha_ann = regression.annualized_alpha
        beta_v = regression.periodic_beta
        alpha_row = regression.inference[0]
        beta_row = regression.inference[1]
        diag = regression.diagnostics
        lines.append(
            f"CAPM OLS point estimates: annualized α (arith.) {alpha_ann:.4f}, periodic α "
            f"{regression.periodic_alpha:.6f}, β {beta_v:.4f}, R² {regression.r_squared:.4f} "
            f"(n={regression.n_obs})."
        )
        lines.append(
            f"Alpha inference — OLS p-value {alpha_row.p_value_ols:.4f}, "
            f"95% CI [{alpha_row.ci_low_ols:.6f}, {alpha_row.ci_high_ols:.6f}] (periodic); "
            f"HAC p-value {alpha_row.p_value_hac:.4f}, "
            f"HAC 95% CI [{alpha_row.ci_low_hac:.6f}, {alpha_row.ci_high_hac:.6f}] "
            f"(Newey–West lags={regression.hac_lags}). Coefficients identical under OLS and HAC."
        )
        lines.append(
            f"Beta inference — OLS p-value {beta_row.p_value_ols:.4f}; HAC p-value {beta_row.p_value_hac:.4f}."
        )
        lines.append(
            f"Model diagnostics (OLS only, not HAC-robust): F-statistic {diag.f_statistic:.3f} "
            f"(p={diag.f_pvalue:.4g}), Durbin–Watson {diag.durbin_watson:.3f} "
            "(residual autocorrelation may invalidate conventional OLS standard errors)."
        )
        lines.append(
            "A low alpha p-value under OLS alone is not proof of skill; use HAC and economic magnitude together."
        )
    else:
        lines.append("CAPM regression not computed (insufficient data or constant benchmark excess returns).")

    if n_obs < 60:
        lines.append(
            f"Sample size ({n_obs}) is modest; rolling and inference results may be imprecise."
        )

    if regime_warning:
        lines.append(regime_warning)

    lines.append(
        "Interpretation: metrics describe historical alignment of portfolio and benchmark returns only; "
        "unobserved factors and selection bias are not modeled."
    )
    return lines
