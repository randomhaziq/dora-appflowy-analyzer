from __future__ import annotations

import argparse

import pandas as pd

from .calculate_metrics import calculate_metrics
from .collect_commits import collect_commits_between_deployments
from .collect_issues import collect_issues
from .collect_releases import collect_releases
from .config import AppConfig, ensure_directories
from .generate_charts import generate_charts
from .git_utils import clone_or_update_repository
from .github_api import GitHubApiClient
from .map_fixes import map_fixes, run_szz_lite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze AppFlowy DORA metrics from Git and GitHub telemetry.")
    parser.add_argument("--start-date", dest="start_date", help="Filter data from this date onwards (YYYY-MM-DD).")
    parser.add_argument("--end-date", dest="end_date", help="Filter data up to this date (YYYY-MM-DD).")
    parser.add_argument("--include-prereleases", action="store_true", help="Include prerelease deployments.")
    parser.add_argument(
        "--skip-api-cache-refresh",
        action="store_true",
        help="Reuse cached raw API exports if they already exist.",
    )
    return parser.parse_args()


def run_pipeline(config: AppConfig) -> None:
    ensure_directories(config)
    client = GitHubApiClient(owner=config.owner, repo=config.repo, token=config.github_token)

    print("1. Cloning or updating AppFlowy repository...")
    repo = clone_or_update_repository(config.repo_url, config.local_repo_path)

    print("2. Collecting releases and deployments...")
    _, deployments_df = collect_releases(config, client)

    print("3. Collecting commits between deployments...")
    commits_df = collect_commits_between_deployments(config, repo, deployments_df)

    print("4. Collecting closed bug issues...")
    _, failures_df = collect_issues(config, client)

    print("5. Mapping fixes and recovery deployments...")
    fix_mappings_df, recovery_df = map_fixes(config, repo, failures_df, deployments_df, client)

    print("6. Running optional SZZ-lite...")
    run_szz_lite(repo, fix_mappings_df, config.processed_data_dir / "szz_lite_results.csv")

    print("7. Calculating metrics...")
    monthly_metrics, yearly_metrics, _ = calculate_metrics(config, deployments_df, commits_df, recovery_df)

    print("8. Generating charts...")
    generate_charts(config, monthly_metrics, yearly_metrics)

    print("Pipeline complete.")
    print(f"Deployments analyzed: {len(deployments_df)}")
    print(f"Commit rows collected: {len(commits_df)}")
    print(f"Failures analyzed: {len(failures_df)}")


def main() -> None:
    args = parse_args()
    base_config = AppConfig()
    include_prereleases = base_config.include_prereleases or args.include_prereleases
    config = base_config.with_overrides(
        start_date=args.start_date,
        end_date=args.end_date,
        include_prereleases=include_prereleases,
        skip_api_cache_refresh=args.skip_api_cache_refresh,
    )
    try:
        run_pipeline(config)
    except Exception as exc:
        raise SystemExit(f"Pipeline failed: {exc}") from exc


if __name__ == "__main__":
    main()
