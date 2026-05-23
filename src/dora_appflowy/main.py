from __future__ import annotations

import argparse
import json

import pandas as pd

from .calculate_metrics import calculate_metrics, export_combined_metrics
from .collect_commits import collect_commits_between_deployments
from .collect_issues import collect_issues
from .collect_releases import collect_releases
from .config import AppConfig, REPOSITORIES, build_repository_configs, combined_results_dir, ensure_directories
from .generate_charts import generate_charts, generate_comparison_charts
from .git_utils import clone_or_update_repository
from .github_api import GitHubApiClient
from .map_fixes import map_fixes, run_szz_lite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze DORA metrics from Git and GitHub telemetry.")
    parser.add_argument("--start-date", dest="start_date", help="Filter data from this date onwards (YYYY-MM-DD).")
    parser.add_argument("--end-date", dest="end_date", help="Filter data up to this date (YYYY-MM-DD).")
    parser.add_argument("--include-prereleases", action="store_true", help="Include prerelease deployments.")
    parser.add_argument(
        "--skip-api-cache-refresh",
        action="store_true",
        help="Reuse cached raw API exports if they already exist.",
    )
    parser.add_argument(
        "--repository",
        dest="repositories",
        action="append",
        choices=sorted(REPOSITORIES),
        help="Run the pipeline for a specific repository slug. Repeat to select multiple repositories.",
    )
    return parser.parse_args()


def run_pipeline(config: AppConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    ensure_directories(config)
    client = GitHubApiClient(owner=config.owner, repo=config.repo, token=config.github_token)

    print(f"1. Cloning or updating {config.repository_name} repository...")
    repo = clone_or_update_repository(config.repo_url, config.local_repo_path)

    print(f"2. Collecting releases and deployments for {config.repository_name}...")
    _, deployments_df = collect_releases(config, client)

    print(f"3. Collecting commits between deployments for {config.repository_name}...")
    commits_df = collect_commits_between_deployments(config, repo, deployments_df)

    print(f"4. Collecting closed bug issues for {config.repository_name}...")
    _, failures_df = collect_issues(config, client)

    print(f"5. Mapping fixes and recovery deployments for {config.repository_name}...")
    fix_mappings_df, recovery_df = map_fixes(config, repo, failures_df, deployments_df, client)

    print(f"6. Running optional SZZ-lite for {config.repository_name}...")
    run_szz_lite(repo, fix_mappings_df, config.processed_data_dir / "szz_lite_results.csv")

    print(f"7. Calculating metrics for {config.repository_name}...")
    monthly_metrics, yearly_metrics, summary = calculate_metrics(config, deployments_df, commits_df, recovery_df)

    print(f"8. Generating charts for {config.repository_name}...")
    generate_charts(config, monthly_metrics, yearly_metrics)

    print(f"Pipeline complete for {config.repository_name}.")
    print(f"Deployments analyzed: {len(deployments_df)}")
    print(f"Commit rows collected: {len(commits_df)}")
    print(f"Failures analyzed: {len(failures_df)}")

    return monthly_metrics, yearly_metrics, summary


def write_combined_summary(config: AppConfig, repo_summaries: list[dict[str, object]]) -> None:
    summary_path = combined_results_dir(config) / "summary_all_repos.json"
    payload = {
        "repositories": repo_summaries,
        "repository_count": len(repo_summaries),
        "repository_slugs": [summary["repository_slug"] for summary in repo_summaries],
    }
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def main() -> None:
    args = parse_args()
    base_config = AppConfig()
    include_prereleases = base_config.include_prereleases or args.include_prereleases
    base_config = base_config.with_overrides(
        start_date=args.start_date,
        end_date=args.end_date,
        include_prereleases=include_prereleases,
        skip_api_cache_refresh=args.skip_api_cache_refresh,
    )

    try:
        configs = build_repository_configs(base_config, args.repositories)
        monthly_frames: list[pd.DataFrame] = []
        yearly_frames: list[pd.DataFrame] = []
        summaries: list[dict[str, object]] = []

        for config in configs:
            monthly_metrics, yearly_metrics, summary = run_pipeline(config)
            monthly_frames.append(monthly_metrics)
            yearly_frames.append(yearly_metrics)
            summaries.append(summary)

        combined_monthly, combined_yearly = export_combined_metrics(base_config, monthly_frames, yearly_frames)
        generate_comparison_charts(base_config, combined_monthly, combined_yearly)
        write_combined_summary(base_config, summaries)
    except Exception as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc


if __name__ == "__main__":
    main()
