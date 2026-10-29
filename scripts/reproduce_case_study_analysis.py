#!/usr/bin/env python3
"""
Reproduce case-study metrics from a local CSV and compare to research/case_study_manifest.json.

Usage:
  python scripts/reproduce_case_study_analysis.py
  python scripts/reproduce_case_study_analysis.py --csv data/case_study_qqq_spy.csv
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantlens.data import validate_and_align
from quantlens.metrics import compute_all_metrics
from quantlens.regime import analyze_regimes
from quantlens.regression import run_capm_regression


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "data" / "case_study_qqq_spy.csv",
    )
    args = parser.parse_args()
    manifest = json.loads((ROOT / "research" / "case_study_manifest.json").read_text())

    if not args.csv.is_file():
        raise SystemExit(
            f"Missing {args.csv}.\n"
            f"Fetch: {manifest.get('fetch_command', 'python scripts/fetch_case_study_csv.py')}"
        )

    digest = hashlib.sha256(args.csv.read_bytes()).hexdigest()
    print(f"SHA256: {digest}")
    exp_sha = manifest["expected"].get("sha256")
    if exp_sha and digest != exp_sha:
        print("WARNING: SHA256 differs from 2026-10-29 manifest (Yahoo series may have revised).")

    settings = manifest["quantlens_settings"]
    data = validate_and_align(
        args.csv.read_bytes(),
        annual_risk_free_rate=float(settings["annual_risk_free_rate"]),
        periods_per_year=int(settings["periods_per_year"]),
    )
    print(
        f"Aligned rows: {data.report.n_rows_aligned} "
        f"({data.dates[0].date()} → {data.dates[-1].date()})"
    )

    metrics = compute_all_metrics(
        data,
        periods_per_year=int(settings["periods_per_year"]),
        var_confidence=float(settings["var_confidence"]),
    )
    reg = run_capm_regression(data, periods_per_year=int(settings["periods_per_year"]))
    regimes = analyze_regimes(data)

    mismatches = 0

    def check(name: str, got: float | None, ref: float, tol: float = 1e-6) -> None:
        nonlocal mismatches
        if got is None:
            print(f"  {name}: MISSING (ref {ref})")
            mismatches += 1
            return
        ok = abs(got - ref) <= tol
        if not ok:
            mismatches += 1
        print(f"  {name}: {got} (ref {ref}) [{'OK' if ok else 'MISMATCH'}]")

    print("Metrics vs manifest:")
    for key, ref in manifest["reference_metrics"].items():
        check(key, metrics.get(key), ref)

    if reg:
        print("Regression vs manifest:")
        ref_r = manifest["reference_regression"]
        check("r_squared", reg.r_squared, ref_r["r_squared"])
        check("periodic_alpha", reg.periodic_alpha, ref_r["periodic_alpha"])
        check("annualized_alpha", reg.annualized_alpha, ref_r["annualized_alpha"])
        check("periodic_beta", reg.periodic_beta, ref_r["periodic_beta"])
        check("ols_p_alpha", reg.inference[0].p_value_ols, ref_r["ols_p_alpha"], tol=1e-4)
        check("hac_p_alpha", reg.inference[0].p_value_hac, ref_r["hac_p_alpha"], tol=1e-4)

    ref_reg = manifest["reference_regimes"]
    print(
        f"Regimes: up={regimes.up.n_obs} (ref {ref_reg['benchmark_up_days']}) "
        f"down={regimes.down.n_obs} (ref {ref_reg['benchmark_down_days']})"
    )
    if regimes.up.n_obs != ref_reg["benchmark_up_days"]:
        mismatches += 1

    raise SystemExit(1 if mismatches else 0)


if __name__ == "__main__":
    main()
