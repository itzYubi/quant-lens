# Historical case study (research deliverable)

This folder holds documentation and optional scripts to build a **reproducible historical** returns dataset for QuantLens. The main app stays offline-friendly; nothing here runs automatically on deploy.

## Contents

| File | Purpose |
|------|---------|
| [HISTORICAL_CASE_STUDY.md](./HISTORICAL_CASE_STUDY.md) | Methodology, data sources, assumptions, reproduction steps |
| [../scripts/fetch_case_study_csv.py](../scripts/fetch_case_study_csv.py) | Optional fetch script (requires `yfinance`) |
| [case_study_manifest.json](./case_study_manifest.json) | Reference numerics and SHA256 for verification |
| [../docs/case-study-qqq-spy.md](../docs/case-study-qqq-spy.md) | Full case study for reviewers |

The bundled `data/sample_returns.csv` remains **synthetic** for demos and unit tests. Do not treat it as market history.

## Quick start

1. Read `HISTORICAL_CASE_STUDY.md`.
2. Optionally run the fetch script (requires network and extra packages).
3. Upload the generated CSV in QuantLens or validate it with `validate_and_align`.
