# Multi-Repository DORA Metrics Analyzer

This project is a Python 3.11 telemetry mining pipeline for a university DevOps Software Quality Assurance group project. It applies the methodology from the article "A Framework for Automating the Measurement of DevOps Research and Assessment (DORA) Metrics" to public GitHub repositories and compares DORA-style metrics across:

- `AppFlowy-IO/AppFlowy`
- `grafana/grafana`
- `keycloak/keycloak`

The analyzer mines Git and GitHub telemetry to estimate:

- Deployment Frequency
- Lead Time for Changes
- Mean Time to Recover
- `adapted_bugfix_deployment_rate` as a practical proxy for Change Failure Rate

## Methodology Notes

Reused ideas from the paper:

- Semantic versioning releases and tags as deployments
- Git commit history for change lead time
- Closed bug-labelled GitHub issues as failures
- Git and GitHub telemetry as the main evidence source

Practical approximations used here:

- Exact Change Failure Rate is not claimed unless full bug-inducing commit detection is available
- A fallback proxy called `adapted_bugfix_deployment_rate` is computed instead
- Optional `SZZ-lite` logic is included as an experimental best-effort step

## Supported Repositories

The pipeline supports these repository slugs:

- `appflowy`
- `grafana`
- `keycloak`

By default, running the main entry point analyzes all three repositories and then generates combined comparison outputs.

## Installation

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a local environment file:

```bash
copy .env.example .env
```

4. Optionally set `GITHUB_TOKEN` in `.env` to reduce API rate-limit issues.

## Usage

Run the full multi-repository pipeline from the repository root:

```bash
python -m dora_appflowy.main
```

Run only selected repositories:

```bash
python -m dora_appflowy.main --repository appflowy --repository grafana
```

Filter by date range:

```bash
python -m dora_appflowy.main --start-date 2024-01-01 --end-date 2025-12-31
```

Include prereleases:

```bash
python -m dora_appflowy.main --include-prereleases
```

Reuse cached API data:

```bash
python -m dora_appflowy.main --skip-api-cache-refresh
```

## Output Structure

Raw API exports are stored per repository:

- `data/raw/appflowy/`
- `data/raw/grafana/`
- `data/raw/keycloak/`

Processed datasets are stored per repository:

- `data/processed/<repository_slug>/`

Final metrics are stored per repository plus a combined folder:

- `data/results/appflowy/`
- `data/results/grafana/`
- `data/results/keycloak/`
- `data/results/combined/`

Charts are stored per repository plus a combined folder:

- `charts/appflowy/`
- `charts/grafana/`
- `charts/keycloak/`
- `charts/combined/`

## Generated Files

Per repository:

- `data/results/<repository_slug>/dora_metrics_monthly.csv`
- `data/results/<repository_slug>/dora_metrics_yearly.csv`
- `data/results/<repository_slug>/summary.json`
- `charts/<repository_slug>/deployment_frequency_monthly.png`
- `charts/<repository_slug>/deployment_frequency_yearly.png`
- `charts/<repository_slug>/lead_time_monthly.png`
- `charts/<repository_slug>/lead_time_yearly.png`
- `charts/<repository_slug>/mttr_monthly.png`
- `charts/<repository_slug>/mttr_yearly.png`
- `charts/<repository_slug>/adapted_cfr_monthly.png`
- `charts/<repository_slug>/adapted_cfr_yearly.png`

Combined:

- `data/results/combined/dora_metrics_monthly_all_repos.csv`
- `data/results/combined/dora_metrics_yearly_all_repos.csv`
- `data/results/combined/summary_all_repos.json`
- `charts/combined/deployment_frequency_monthly_comparison.png`
- `charts/combined/deployment_frequency_yearly_comparison.png`
- `charts/combined/lead_time_monthly_comparison.png`
- `charts/combined/lead_time_yearly_comparison.png`
- `charts/combined/mttr_monthly_comparison.png`
- `charts/combined/mttr_yearly_comparison.png`
- `charts/combined/adapted_cfr_monthly_comparison.png`
- `charts/combined/adapted_cfr_yearly_comparison.png`

## Comparison Guidance

Cross-repository charts are useful, but they should be interpreted carefully:

- Release and tag practices differ across repositories
- Bug labels may not be applied consistently across projects
- Fix-closing keywords and deployment tagging conventions affect mapping quality
- `adapted_bugfix_deployment_rate` is still a proxy, not the paper's exact Change Failure Rate

The project aims to keep the methodology consistent across repositories so the comparisons are fairer, even when the underlying telemetry is imperfect.

## Testing

```bash
python -m pytest
```
