"""Plotly chart builders."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quantlens.metrics import cumulative_wealth, drawdown_series


def growth_chart(
    dates: pd.DatetimeIndex,
    portfolio: pd.Series,
    benchmark: pd.Series,
) -> go.Figure:
    wp = cumulative_wealth(portfolio)
    wb = cumulative_wealth(benchmark)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=dates, y=wp, name="Portfolio wealth", mode="lines")
    )
    fig.add_trace(
        go.Scatter(x=dates, y=wb, name="Benchmark wealth", mode="lines")
    )
    fig.update_layout(
        title="Cumulative growth (wealth index, start = 1)",
        xaxis_title="Date",
        yaxis_title="Wealth index",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    return fig


def drawdown_chart(dates: pd.DatetimeIndex, portfolio: pd.Series) -> go.Figure:
    wealth = cumulative_wealth(portfolio)
    dd = drawdown_series(wealth)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=dd,
            name="Drawdown",
            fill="tozeroy",
            mode="lines",
        )
    )
    fig.update_layout(
        title="Portfolio drawdown",
        xaxis_title="Date",
        yaxis_title="Drawdown (fraction)",
        hovermode="x unified",
    )
    return fig


def rolling_chart(
    dates: pd.DatetimeIndex,
    series_map: dict[str, pd.Series],
    title: str,
    y_title: str,
) -> go.Figure:
    fig = go.Figure()
    for name, s in series_map.items():
        fig.add_trace(go.Scatter(x=dates, y=s, name=name, mode="lines"))
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_title,
        hovermode="x unified",
    )
    return fig


def regime_bar_chart(
    up_mean: float,
    down_mean: float,
    up_n: int,
    down_n: int,
) -> go.Figure:
    fig = go.Figure(
        data=[
            go.Bar(
                x=[f"Benchmark ≥ 0 (n={up_n})", f"Benchmark < 0 (n={down_n})"],
                y=[up_mean, down_mean],
                name="Mean portfolio return (periodic)",
            )
        ]
    )
    fig.update_layout(
        title="Descriptive regime split: mean portfolio return by benchmark sign",
        yaxis_title="Mean periodic return",
    )
    return fig
