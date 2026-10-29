"""Descriptive benchmark up/down regime comparison (not predictive)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quantlens.data import AlignedReturns


@dataclass
class RegimeStats:
    regime: str
    n_obs: int
    mean_portfolio: float
    mean_benchmark: float
    mean_active: float
    ann_vol_portfolio: float | None


@dataclass
class RegimeAnalysis:
    up: RegimeStats
    down: RegimeStats
    min_group_warning: str | None


def analyze_regimes(
    data: AlignedReturns,
    *,
    periods_per_year: int = 252,
    min_group_size: int = 10,
) -> RegimeAnalysis:
    """
    Split observations by sign of benchmark return (zero counted as up).

    Descriptive only — not a latent regime model.
    """
    p = data.portfolio_return
    b = data.benchmark_return
    active = p - b

    up_mask = b >= 0
    down_mask = b < 0

    def _stats(name: str, mask: pd.Series) -> RegimeStats:
        sub_p = p[mask]
        sub_b = b[mask]
        sub_a = active[mask]
        n = len(sub_p)
        vol = None
        if n >= 2:
            vol = float(sub_p.std(ddof=1) * (periods_per_year**0.5))
        return RegimeStats(
            regime=name,
            n_obs=n,
            mean_portfolio=float(sub_p.mean()) if n else 0.0,
            mean_benchmark=float(sub_b.mean()) if n else 0.0,
            mean_active=float(sub_a.mean()) if n else 0.0,
            ann_vol_portfolio=vol,
        )

    up = _stats("benchmark_return >= 0", up_mask)
    down = _stats("benchmark_return < 0", down_mask)

    warning = None
    small = []
    if up.n_obs < min_group_size:
        small.append(f"up ({up.n_obs})")
    if down.n_obs < min_group_size:
        small.append(f"down ({down.n_obs})")
    if small:
        warning = (
            "Small sample in regime group(s): "
            + ", ".join(small)
            + f". Interpretation is limited (minimum suggested: {min_group_size})."
        )

    return RegimeAnalysis(up=up, down=down, min_group_warning=warning)
