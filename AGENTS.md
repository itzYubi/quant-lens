# QuantLens — Cursor Agent Instructions

## Mission

Build QuantLens, a polished, research-oriented portfolio analytics and risk application. The user wants a functional MVP in one day and wants Cursor AI to generate the code. Prioritize correct quantitative methods, a usable UI, tests, and documentation over infrastructure.

Do not stop at a plan or scaffold. Inspect the repository, implement the application, run available checks, fix failures, and summarize what works and what remains.

## Product scope

Create a local web app where a user uploads a CSV containing dated portfolio returns and benchmark returns. The app validates the data and produces a reproducible performance, risk, and regression report.

Required MVP features:
- CSV upload and helpful validation/error messages.
- Configurable annual risk-free rate and trading-days-per-year convention (default 252).
- Portfolio and benchmark cumulative growth charts.
- Drawdown chart.
- Metrics table with definitions and units.
- CAPM regression results with alpha, beta, R-squared, standard errors, p-values, and confidence intervals where statistically valid.
- Rolling beta and rolling volatility charts when sufficient observations exist.
- Historical Value at Risk (VaR) and Expected Shortfall (CVaR/ES), clearly labelled with confidence level and loss sign convention.
- Downloadable metrics report (CSV or JSON) and a downloadable sample CSV.
- A sample dataset included in the repository so the app can be tried immediately.
- Automated tests for key formulas, edge cases, and input validation.
- Clear README with setup, run, assumptions, formulas, limitations, and example CSV.

## Technology and architecture

Use:
- Python 3.11+ (target Python 3.11 or 3.12 unless the environment dictates otherwise)
- Streamlit for UI
- pandas and NumPy for data handling
- SciPy and statsmodels for statistical analysis
- Plotly for interactive charts
- pytest for tests

Keep the architecture lightweight and modular. No database, authentication, paid APIs, cloud deployment, or separate backend for the MVP.

Suggested structure:
- `app.py` — Streamlit UI and orchestration
- `quantlens/data.py` — CSV parsing, validation, return alignment
- `quantlens/metrics.py` — performance and risk metrics
- `quantlens/regression.py` — CAPM regression and inference
- `quantlens/charts.py` — reusable charts, if useful
- `tests/` — pytest tests
- `data/sample_returns.csv` — deterministic example data
- `requirements.txt`
- `README.md`
- `.gitignore`

Adapt if the repository already has a sensible structure. Avoid unnecessary abstractions.

## Input format and data handling

Support CSV columns:
- `date`
- `portfolio_return`
- `benchmark_return`
- optional `risk_free_rate`

Accept decimal returns by default: `0.01` means +1%. Make this explicit in the UI and README. If an annual risk-free rate is entered in the UI, convert it to an equivalent per-period rate consistently; document the convention. If a per-row risk-free-rate column exists, define whether it is per-period or annualized and do not silently mix conventions.

Validate:
- required columns and parseable dates
- duplicate dates
- missing/non-numeric return values
- impossible simple returns at or below -100%
- adequate observation count for each metric
- constant series / zero volatility
- empty file and malformed CSV
- non-overlapping or misaligned dates

Sort chronologically. Align portfolio, benchmark, and risk-free observations by date. Do not silently fill missing return values with zero. Report dropped rows and why. Handle short histories gracefully; disable rolling charts or regression inference when insufficient data rather than fabricating results.

Do not automatically download market data. The app should work offline using the supplied sample CSV.

## Quantitative definitions and correctness

Document each metric's exact definition, assumptions, units, and annualization convention in code/docstrings and README. Use consistent, aligned observations.

Use `periods_per_year = 252` by default for daily trading-day returns; expose the convention in the UI.

Implement at least:

### Performance
- Cumulative growth: compound simple returns using cumulative product of `(1 + r)`.
- CAGR: `(ending_growth / beginning_growth) ** (periods_per_year / n) - 1`, where `n` is the number of return observations and the growth index begins at 1. Handle nonpositive ending wealth and insufficient samples clearly.
- Annualized arithmetic return: mean periodic return times periods per year; label distinctly from CAGR.
- Annualized volatility: sample standard deviation (`ddof=1`) times `sqrt(periods_per_year)`.

### Risk-adjusted and relative performance
- Sharpe: annualized mean periodic excess return divided by annualized volatility, using a consistent periodic risk-free rate.
- Sortino: annualized mean periodic excess return divided by annualized downside deviation. State the target/minimum acceptable return used in the downside calculation; do not hide the convention.
- Beta: covariance of portfolio and benchmark excess returns divided by variance of benchmark excess returns. If no risk-free series is supplied, use zero risk-free rate for beta or make the convention explicit and consistent.
- Jensen's alpha / CAPM: regress portfolio excess returns on benchmark excess returns. Report the periodic intercept and annualized arithmetic intercept (`periodic_alpha * periods_per_year`) and label both. Do not confuse annualized regression alpha with CAGR difference.
- R-squared from regression.
- Tracking error: sample standard deviation of periodic active returns times `sqrt(periods_per_year)`.
- Information ratio: annualized arithmetic mean active return divided by annualized tracking error.
- Maximum drawdown: minimum of wealth divided by its running peak minus one; clearly define whether the initial wealth of 1 is included as a peak.
- VaR and expected shortfall: use historical empirical quantiles. Define whether output is a positive loss number or a negative return threshold and keep labels consistent. Expected shortfall should be based on observations in the loss tail and documented carefully.

### Statistical analysis
- Use `statsmodels` or an equivalent transparent implementation for OLS CAPM regression.
- Report coefficient standard errors, p-values, and 95% confidence intervals when the sample supports inference.
- Explain that conventional OLS inference may be unreliable with heteroskedasticity/autocorrelation; if time permits, offer Newey–West/HAC standard errors as an optional reported estimate. Do not claim statistical significance without the relevant uncertainty estimate.
- Rolling beta (default 60 observations) and rolling volatility should require enough observations and display the chosen window.
- Make clear that historical metrics are descriptive, not forecasts or guarantees.

Never use hardcoded/example metric values in the live dashboard. All displayed values must be computed from uploaded or sample data. Do not fabricate results.

## UI expectations

Create a clean, professional, finance/research-style interface:
- App title: QuantLens — Portfolio Analytics & Risk Research
- Sidebar controls for risk-free rate, annualization, confidence level, and rolling window.
- Clear success/error/warning messages.
- KPI cards for key results, with units and sensible percentage/decimal formatting.
- Tabs or sections for Overview, Risk, Regression, and Data Quality.
- Interactive Plotly charts with titles, axis labels, and hover information.
- Explain metrics in plain language using tooltips, captions, or an expandable methodology section.
- Keep the layout responsive and avoid clutter.
- Avoid implying the tool provides financial advice.

## Tests and quality bar

Write deterministic tests for:
- cumulative growth and CAGR using hand-calculable return series
- annualized volatility
- Sharpe and zero-volatility behavior
- beta for a known synthetic relationship
- regression alpha/beta on a deterministic synthetic dataset
- max drawdown including the initial wealth peak
- VaR and expected shortfall convention
- invalid columns, duplicate dates, missing values, and impossible returns
- short sample behavior and constant benchmark behavior

Use deterministic synthetic test data with fixed seeds where random data is necessary. Do not test only that functions execute; assert expected numerical values or invariants. Avoid look-ahead bias in any rolling metric.

## README and deliverables

README should include:
- project purpose and features
- screenshot placeholder or instructions for taking a screenshot (do not invent a screenshot)
- prerequisites and macOS setup
- virtual environment creation and dependency installation
- launch command
- CSV schema and decimal return convention
- formula/methodology notes and annualization assumptions
- testing command
- limitations and future improvements

Include a `requirements.txt` with direct dependencies only. Add a `.gitignore` for Python caches, virtual environments, Streamlit secrets, and editor/OS clutter. Never add secrets or API keys.

## Cursor workflow

1. Inspect the current workspace before changing files.
2. If it is empty, create the proposed structure.
3. Implement the complete MVP rather than only describing it.
4. Run `python -m pytest -q` (or the available equivalent).
5. Fix test failures and run the tests again.
6. Run basic import/syntax checks and identify any remaining runtime limitation.
7. Do not claim tests passed unless they were actually run and passed.
8. If a command requires user approval, explain the command and wait for approval rather than pretending it ran.
9. At completion, report files created, features implemented, exact test result, and the command to launch the app on macOS.

## Priorities if time is running out

Priority 1: correct core metrics and input validation.
Priority 2: tests and statistical regression.
Priority 3: usable dashboard and charts.
Priority 4: report download and polish.

Do not sacrifice financial correctness to add extra features. Do not add a strategy backtester or optimization engine to the one-day MVP unless all required features above are complete and tested.


## Deployment target: free Streamlit Community Cloud

The intended public demo should be deployed on Streamlit Community Cloud from a GitHub repository. Keep deployment simple and compatible with the free tier.

Requirements:
- Keep the application stateless; uploaded CSVs should be processed in memory and not persisted to disk or a database unless explicitly required later.
- Do not add a database, external market-data API, paid service, authentication system, or cloud infrastructure for the MVP.
- Ensure the app can start from the repository root with `streamlit run app.py`.
- Keep `requirements.txt` complete and compatible with the selected Python version. Avoid unnecessary packages and platform-specific dependencies.
- Include a repository-root `README.md` section for deployment:
  1. Push the project to a GitHub repository.
  2. Open https://share.streamlit.io/ and connect/select the repository.
  3. Choose the branch and `app.py` as the main file.
  4. Deploy and verify the public URL.
- Document that Streamlit Community Cloud free-tier resource limits and sleep behavior can change; do not promise uptime, performance, or specific quotas.
- Never commit secrets, tokens, private financial data, local virtual environments, caches, or uploaded user CSVs.
- Include a small, clearly labelled synthetic sample dataset for visitors to try without uploading their own data.
- Make the dashboard usable in a fresh hosted environment and show clear errors if an uploaded file cannot be parsed.
- Before claiming deployment is complete, verify the repository is configured for deployment and distinguish local test success from a live deployment. Do not claim to have deployed or tested a public URL unless actually done.


## Project differentiation and research objectives

### Positioning

QuantLens is not merely a calculator for standard portfolio metrics. Position it as a **Portfolio Risk, Alpha Robustness, and Regime Analysis Lab**. Its central research question is:

"Does a portfolio outperform its benchmark on a risk-adjusted basis, or can its apparent performance be explained by market exposure, unstable risk, or a small number of unusually strong periods?"

Do not claim the methods themselves are novel. The differentiation is the coherent, reproducible combination of transparent calculations, statistical uncertainty, rolling analysis, sensitivity checks, and evidence-based interpretation.

### Required differentiating features

1. **Alpha robustness**
   - Estimate CAPM alpha and beta from aligned portfolio and benchmark excess returns.
   - Show coefficient estimates, conventional OLS standard errors, p-values, and 95% confidence intervals where appropriate.
   - Add Newey–West/HAC standard errors as a second inference option, with a documented lag choice and an explanation of why autocorrelation/heteroskedasticity may affect uncertainty estimates.
   - Present OLS and HAC inference side by side; do not imply HAC changes the coefficient estimates.
   - Distinguish statistical evidence from economic significance. Never label alpha "proven" or "genuine" solely because the point estimate is positive.

2. **Rolling risk stability**
   - Plot rolling beta and annualized volatility; include rolling Sharpe if the observation count and risk-free inputs support it.
   - Make the rolling window configurable and clearly label it.
   - Do not calculate a rolling estimate until a full window is available; never use future observations in a rolling value.

3. **Descriptive market-regime analysis**
   - Compare portfolio and benchmark behavior in positive-benchmark-return versus negative-benchmark-return periods.
   - Clearly label this as a simple descriptive classification based on observed returns, not a predictive regime model.
   - Show sample counts in each regime and warn when a group is too small for meaningful interpretation.
   - Avoid causal claims and avoid implying that this classification identifies latent economic regimes.

4. **Sensitivity and robustness checks**
   - Compare results across reasonable subperiods or evaluation windows when sample length permits.
   - Show whether alpha and key risk measures are sensitive to the selected period.
   - Optionally show the effect of excluding the most extreme portfolio-return observations as a clearly labelled diagnostic, not as the primary result. Never silently remove outliers from the main calculations.
   - Warn about short samples, missing observations, outliers, and low statistical power.

5. **Evidence-based research summary**
   - Create a concise report summarizing calculated findings, not invented narratives.
   - Every generated statement must be traceable to actual metrics, regression outputs, sample counts, or data-quality checks.
   - Distinguish observed performance, statistical uncertainty, and interpretation.
   - Use cautious language. If estimates are imprecise or samples are small, state that the available data are insufficient for a strong conclusion.
   - Do not use an external LLM or paid API to generate conclusions. The report can use deterministic templates based on computed results.

### Reproducible case study

- Include a small synthetic dataset for immediate UI exploration and automated tests.
- If actual historical market data is used for a case study, document the source, retrieval date, tickers/series, date range, return frequency, adjustment assumptions, and any transformations.
- Do not fabricate a real-data study or represent synthetic data as historical market data.
- Keep external data retrieval optional; the app must remain usable offline with its sample dataset.
- Include a reproducible case-study note in the README. If the one-day scope does not allow a properly sourced historical case study, document this as a next step rather than pretending it has been completed.

### Scope and interpretation limits

- With only portfolio and benchmark returns, QuantLens can estimate benchmark-relative performance and assess uncertainty, but cannot prove manager skill or identify unobserved factor exposures.
- Do not call a positive alpha "genuine alpha" without qualification. Use terms such as "estimated alpha" and "evidence for nonzero alpha."
- Do not claim the project or methods are original to QuantLens. The contribution is transparent implementation, integration, reproducibility, and interpretation.
- Prioritize core metric correctness, OLS/HAC inference, rolling risk analysis, automated tests, and honest reporting before regime analysis or optional outlier diagnostics.
