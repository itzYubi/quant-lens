"""QuantLens — Portfolio Analytics & Risk Research."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from quantlens.charts import (
    drawdown_chart,
    growth_chart,
    regime_bar_chart,
    rolling_chart,
)
from quantlens.data import DataValidationError, aligned_to_frame, validate_and_align
from quantlens.metrics import (
    compute_all_metrics,
    metrics_table_rows,
    rolling_beta,
    rolling_sharpe,
    rolling_volatility,
)
from quantlens.regime import analyze_regimes
from quantlens.regression import regression_to_dict, run_capm_regression
from quantlens.report import (
    build_research_summary,
    outlier_alpha_diagnostic,
    split_subperiods,
)
from quantlens.glossary import filter_glossary

SAMPLE_PATH = Path(__file__).parent / "data" / "sample_returns.csv"

st.set_page_config(
    page_title="QuantLens",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("QuantLens — Portfolio Analytics & Risk Research")
st.caption(
    "Upload dated portfolio and benchmark **decimal** returns (e.g. `0.01` = +1%). "
    "This tool is for research and education — not financial advice."
)


def load_source(uploaded, use_sample: bool) -> bytes | str | None:
    if uploaded is not None:
        return uploaded.getvalue()
    if use_sample:
        return SAMPLE_PATH.read_bytes()
    return None


with st.sidebar:
    st.header("Settings")
    annual_rf_pct = st.number_input(
        "Annual risk-free rate (%)",
        min_value=0.0,
        max_value=50.0,
        value=4.0,
        step=0.25,
        format="%.2f",
        help="Converted to decimal per period as (rate% / 100) / periods per year unless CSV has per-row RF.",
    )
    annual_rf = annual_rf_pct / 100.0
    periods_per_year = st.number_input(
        "Periods per year (annualization)",
        min_value=1,
        max_value=365,
        value=252,
        step=1,
    )
    var_confidence = st.slider(
        "VaR / ES confidence level",
        min_value=0.80,
        max_value=0.99,
        value=0.95,
        step=0.01,
    )
    rolling_window = st.number_input(
        "Rolling window (observations)",
        min_value=10,
        max_value=252,
        value=60,
        step=5,
    )
    rf_col_annual = st.checkbox(
        "CSV `risk_free_rate` column is annualized",
        value=False,
        help="If unchecked, column values are per-period decimal returns.",
    )
    st.divider()
    use_sample = st.toggle("Use bundled synthetic sample data", value=True)
    uploaded = st.file_uploader("Upload returns CSV", type=["csv"])
    if use_sample and uploaded is None:
        st.caption("Sample: synthetic series (RNG seed 42), not real market history.")

st.sidebar.download_button(
    label="Download sample CSV",
    data=SAMPLE_PATH.read_bytes(),
    file_name="sample_returns.csv",
    mime="text/csv",
)

source = load_source(uploaded, use_sample and uploaded is None)

if source is None:
    st.info("Upload a CSV or enable the bundled sample dataset in the sidebar.")
    st.stop()

try:
    aligned = validate_and_align(
        source,
        annual_risk_free_rate=annual_rf,
        periods_per_year=int(periods_per_year),
        risk_free_column_is_annual=rf_col_annual,
    )
except DataValidationError as exc:
    st.error(str(exc))
    st.stop()

for msg in aligned.report.dropped_rows:
    st.warning(msg)
for msg in aligned.report.warnings:
    st.warning(msg)

if not aligned.report.dropped_rows:
    st.success(
        f"Loaded {aligned.report.n_rows_aligned} aligned observations "
        f"({aligned.dates[0].date()} → {aligned.dates[-1].date()})."
    )

if uploaded is not None:
    st.caption(f"**Data source:** uploaded file `{uploaded.name}` (user-provided returns).")
elif use_sample:
    st.caption(
        "**Data source:** bundled **synthetic** sample (`data/sample_returns.csv`, NumPy seed 42). "
        "Not historical market data."
    )

metrics = compute_all_metrics(
    aligned,
    periods_per_year=int(periods_per_year),
    var_confidence=var_confidence,
)
reg = run_capm_regression(aligned, periods_per_year=int(periods_per_year))
regimes = analyze_regimes(aligned, periods_per_year=int(periods_per_year))
subperiods = split_subperiods(
    aligned,
    periods_per_year=int(periods_per_year),
    var_confidence=var_confidence,
)
outlier_diag = outlier_alpha_diagnostic(aligned, periods_per_year=int(periods_per_year))
summary_lines = build_research_summary(
    metrics,
    reg,
    regimes.min_group_warning,
    metrics["n_observations"],
)

# KPI row
k1, k2, k3, k4 = st.columns(4)
with k1:
    cagr = metrics.get("portfolio_cagr")
    st.metric("Portfolio CAGR", f"{cagr:.2%}" if cagr is not None else "N/A")
with k2:
    vol = metrics.get("portfolio_ann_vol")
    st.metric("Ann. volatility", f"{vol:.2%}" if vol is not None else "N/A")
with k3:
    mdd = metrics.get("portfolio_max_drawdown")
    st.metric("Max drawdown", f"{mdd:.2%}" if mdd is not None else "N/A")
with k4:
    if reg:
        st.metric("Est. ann. alpha (OLS)", f"{reg.annualized_alpha:.2%}")
    else:
        st.metric("Est. ann. alpha (OLS)", "N/A")

tab_over, tab_risk, tab_reg, tab_quality, tab_research, tab_glossary = st.tabs(
    ["Overview", "Risk", "Regression", "Data Quality", "Research Summary", "Glossary"]
)

with tab_over:
    st.plotly_chart(
        growth_chart(aligned.dates, aligned.portfolio_return, aligned.benchmark_return),
        use_container_width=True,
    )
    st.plotly_chart(
        drawdown_chart(aligned.dates, aligned.portfolio_return),
        use_container_width=True,
    )
    st.subheader("Metrics")
    st.caption(
        f"Annualization: {int(periods_per_year)} periods/year; "
        f"periodic risk-free = annual rate / {int(periods_per_year)} unless CSV column overrides."
    )
    table_df = pd.DataFrame(metrics_table_rows(metrics))
    st.dataframe(
        table_df[["metric", "display_value", "unit", "definition"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "metric": st.column_config.TextColumn("Metric", width="medium"),
            "display_value": st.column_config.TextColumn("Value"),
            "unit": st.column_config.TextColumn("Unit", width="small"),
            "definition": st.column_config.TextColumn("Definition", width="large"),
        },
    )
    export_df = table_df[["metric_key", "metric", "value_raw", "display_value", "unit", "definition"]]
    export_payload = {
        "metrics": {k: v for k, v in metrics.items() if k != "var_convention"},
        "regression": regression_to_dict(reg) if reg else None,
    }
    st.download_button(
        "Download metrics report (JSON)",
        data=json.dumps(export_payload, indent=2, default=str),
        file_name="quantlens_metrics.json",
        mime="application/json",
    )
    csv_metrics = export_df.to_csv(index=False)
    st.download_button(
        "Download metrics table (CSV)",
        data=csv_metrics,
        file_name="quantlens_metrics.csv",
        mime="text/csv",
    )

with tab_risk:
    st.markdown(
        f"**VaR / ES convention:** historical quantile at {var_confidence:.0%} confidence; "
        "reported as **positive loss magnitude** (fraction of wealth)."
    )
    r1, r2 = st.columns(2)
    with r1:
        st.metric("Historical VaR (loss)", f"{metrics['portfolio_var']:.2%}" if metrics["portfolio_var"] else "N/A")
    with r2:
        st.metric("Expected shortfall", f"{metrics['portfolio_es']:.2%}" if metrics["portfolio_es"] else "N/A")

    n = len(aligned.portfolio_return)
    win = int(rolling_window)
    rf = aligned.risk_free_periodic
    assert rf is not None
    if n >= win:
        rb = rolling_beta(aligned.portfolio_return, aligned.benchmark_return, rf, win)
        rv = rolling_volatility(aligned.portfolio_return, win, int(periods_per_year))
        rs = rolling_sharpe(aligned.portfolio_return, rf, win, int(periods_per_year))
        st.plotly_chart(
            rolling_chart(
                aligned.dates,
                {f"Rolling beta ({win}d)": rb},
                title=f"Rolling beta ({win} observations)",
                y_title="Beta",
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            rolling_chart(
                aligned.dates,
                {f"Rolling vol ({win}d)": rv},
                title=f"Rolling annualized volatility ({win} obs.)",
                y_title="Ann. volatility",
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            rolling_chart(
                aligned.dates,
                {f"Rolling Sharpe ({win}d)": rs},
                title=f"Rolling Sharpe ({win} obs.)",
                y_title="Sharpe ratio",
            ),
            use_container_width=True,
        )
    else:
        st.warning(
            f"Need at least {win} observations for rolling charts; have {n}."
        )

    st.subheader("Descriptive regime analysis")
    st.caption(
        "Simple split by benchmark return sign — not a predictive regime model."
    )
    if regimes.min_group_warning:
        st.warning(regimes.min_group_warning)
    st.plotly_chart(
        regime_bar_chart(
            regimes.up.mean_portfolio,
            regimes.down.mean_portfolio,
            regimes.up.n_obs,
            regimes.down.n_obs,
        ),
        use_container_width=True,
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "regime": regimes.up.regime,
                    "n": regimes.up.n_obs,
                    "mean_portfolio": regimes.up.mean_portfolio,
                    "mean_benchmark": regimes.up.mean_benchmark,
                    "mean_active": regimes.up.mean_active,
                },
                {
                    "regime": regimes.down.regime,
                    "n": regimes.down.n_obs,
                    "mean_portfolio": regimes.down.mean_portfolio,
                    "mean_benchmark": regimes.down.mean_benchmark,
                    "mean_active": regimes.down.mean_active,
                },
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )

with tab_reg:
    if reg is None:
        st.warning("CAPM regression unavailable for this sample.")
    else:
        st.markdown(
            "CAPM: portfolio excess return regressed on benchmark excess return. "
            "**OLS** standard errors assume homoskedastic, uncorrelated errors. "
            f"**HAC (Newey–West)** uses max lags = {reg.hac_lags} as a robustness check; "
            "coefficients are unchanged."
        )
        st.caption(
            "F-statistic and Durbin–Watson below are from the **classical OLS** fit only; "
            "they are not HAC-robust."
        )
        inf_df = pd.DataFrame(
            [
                {
                    "coefficient": r.coefficient,
                    "estimate": r.estimate,
                    "std_err_ols": r.std_err_ols,
                    "p_value_ols": r.p_value_ols,
                    "ci_low_ols": r.ci_low_ols,
                    "ci_high_ols": r.ci_high_ols,
                    "std_err_hac": r.std_err_hac,
                    "p_value_hac": r.p_value_hac,
                    "ci_low_hac": r.ci_low_hac,
                    "ci_high_hac": r.ci_high_hac,
                }
                for r in reg.inference
            ]
        )
        st.dataframe(
            inf_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "estimate": st.column_config.NumberColumn(format="%.6f"),
                "std_err_ols": st.column_config.NumberColumn(format="%.6f"),
                "std_err_hac": st.column_config.NumberColumn(format="%.6f"),
                "p_value_ols": st.column_config.NumberColumn(format="%.4f"),
                "p_value_hac": st.column_config.NumberColumn(format="%.4f"),
                "ci_low_ols": st.column_config.NumberColumn(format="%.6f"),
                "ci_high_ols": st.column_config.NumberColumn(format="%.6f"),
                "ci_low_hac": st.column_config.NumberColumn(format="%.6f"),
                "ci_high_hac": st.column_config.NumberColumn(format="%.6f"),
            },
        )
        d = reg.diagnostics
        st.markdown(
            f"**Diagnostics:** F = {d.f_statistic:.3f} (p = {d.f_pvalue:.4g}), "
            f"Durbin–Watson = {d.durbin_watson:.3f}, "
            f"HAC lags = {d.hac_max_lags} ({d.hac_lag_rule}), "
            f"CI level = {d.confidence_level:.0%}."
        )
        st.write(
            f"R² = {reg.r_squared:.4f} | Adj. R² = {reg.adj_r_squared:.4f} | "
            f"Periodic α = {reg.periodic_alpha:.6f} | "
            f"Annualized α (arith.) = {reg.annualized_alpha:.4f}"
        )
        with st.expander("Full OLS summary"):
            st.text(reg.ols_summary_text)

with tab_quality:
    st.write("**Alignment report**")
    st.json(
        {
            "n_rows_raw": aligned.report.n_rows_raw,
            "n_rows_aligned": aligned.report.n_rows_aligned,
            "dropped_rows": aligned.report.dropped_rows,
            "warnings": aligned.report.warnings,
        }
    )
    st.subheader("Aligned data preview")
    st.dataframe(aligned_to_frame(aligned).head(20), use_container_width=True)
    st.dataframe(aligned_to_frame(aligned).tail(5), use_container_width=True)

with tab_research:
    st.subheader("Evidence-based summary")
    for line in summary_lines:
        st.markdown(f"- {line}")

    if subperiods:
        st.subheader("Subperiod sensitivity (first vs second half)")
        sens_rows = []
        for sp in subperiods:
            sens_rows.append(
                {
                    "period": sp.label,
                    "dates": f"{sp.start} → {sp.end}",
                    "n": sp.n_obs,
                    "alpha_ann": sp.alpha_annualized,
                    "beta": sp.beta,
                    "sharpe": sp.metrics.get("portfolio_sharpe"),
                    "max_dd": sp.metrics.get("portfolio_max_drawdown"),
                }
            )
        st.dataframe(pd.DataFrame(sens_rows), hide_index=True, use_container_width=True)

    if outlier_diag:
        st.subheader("Outlier diagnostic (not primary results)")
        st.caption(outlier_diag.note)
        st.write(
            f"Excluded {outlier_diag.n_excluded} date(s): {', '.join(outlier_diag.excluded_dates)}"
        )
        st.write(
            f"Annualized α full sample: {outlier_diag.alpha_annualized_full} | "
            f"after exclusion: {outlier_diag.alpha_annualized_trimmed}"
        )

with tab_glossary:
    st.subheader("Glossary")
    st.caption(
        "Definitions for metrics, charts, and regression output (including items in the full OLS summary). "
        "Educational reference only."
    )
    glossary_query = st.text_input("Search terms", placeholder="e.g. CAPM, kurtosis, rolling beta")
    sections = filter_glossary(glossary_query)
    if not sections:
        st.info("No matching terms. Try a shorter search or clear the filter.")
    for section_title, entries in sections.items():
        st.markdown(f"### {section_title}")
        for term, definition in entries:
            st.markdown(f"**{term}** — {definition}")

with st.expander("Methodology (brief)"):
    st.markdown(
        """
        - Returns are simple decimals; wealth compounds with ∏(1+r).
        - Annual risk-free rate from sidebar → periodic RF = annual / periods per year.
        - Volatility uses sample std (ddof=1) × √(periods/year) on **returns**; Sharpe uses **excess-return** vol.
        - Sortino: MAR = 0 on simple returns; downside uses excess returns below (MAR − RF).
        - Historical VaR/ES use empirical quantiles; ES averages the tail at or below VaR.
        - Rolling metrics require a full window before plotting (no look-ahead).
        """
    )

st.divider()
st.caption("QuantLens — descriptive analytics only. Past performance does not guarantee future results.")
