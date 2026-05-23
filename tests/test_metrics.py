from __future__ import annotations

import json

import pandas as pd

from dora_appflowy.calculate_metrics import (
    calculate_adapted_cfr,
    calculate_deployment_frequency,
    calculate_lead_time_metrics,
    calculate_metrics,
    export_combined_metrics,
)
from dora_appflowy.config import AppConfig, REPOSITORIES, build_repository_configs


def test_deployment_frequency_calculation() -> None:
    deployments_df = pd.DataFrame(
        {
            "tag_name": ["v1.0.0", "v1.1.0", "v1.2.0"],
            "published_at": ["2024-01-02T00:00:00Z", "2024-01-15T00:00:00Z", "2024-02-01T00:00:00Z"],
        }
    )
    result = calculate_deployment_frequency(deployments_df, "M")
    january = result[result["period"] == "2024-01"]["metric_value"].iloc[0]
    february = result[result["period"] == "2024-02"]["metric_value"].iloc[0]
    assert january == 2
    assert february == 1


def test_lead_time_calculation() -> None:
    commits_df = pd.DataFrame(
        {
            "deployment_date": ["2024-01-10T00:00:00Z", "2024-01-10T00:00:00Z"],
            "lead_time_days": [2.0, 4.0],
        }
    )
    result = calculate_lead_time_metrics(commits_df, "M")
    mean_value = result[result["metric_name"] == "lead_time_days_mean"]["metric_value"].iloc[0]
    assert mean_value == 3.0


def test_adapted_cfr_calculation() -> None:
    deployments_df = pd.DataFrame(
        {
            "tag_name": ["v1.0.0", "v1.1.0"],
            "published_at": ["2024-01-02T00:00:00Z", "2024-01-15T00:00:00Z"],
        }
    )
    recovery_df = pd.DataFrame(
        {
            "recovery_deployment_tag": ["v1.1.0"],
            "recovery_deployment_date": ["2024-01-15T00:00:00Z"],
            "recovery_time_days": [5.0],
        }
    )
    result = calculate_adapted_cfr(deployments_df, recovery_df, "M")
    rate = result["metric_value"].iloc[0]
    assert rate == 0.5


def test_calculate_metrics_writes_repository_aware_outputs(tmp_path) -> None:
    config = AppConfig(
        repository=REPOSITORIES["grafana"],
        root_dir=tmp_path,
        data_dir=tmp_path / "data",
        raw_data_root_dir=tmp_path / "data" / "raw",
        processed_data_root_dir=tmp_path / "data" / "processed",
        results_root_dir=tmp_path / "data" / "results",
        charts_root_dir=tmp_path / "charts",
        cache_dir=tmp_path / ".cache",
    )
    config.results_dir.mkdir(parents=True, exist_ok=True)

    deployments_df = pd.DataFrame(
        {
            "tag_name": ["v1.0.0", "v1.1.0"],
            "published_at": ["2024-01-02T00:00:00Z", "2024-01-15T00:00:00Z"],
        }
    )
    commits_df = pd.DataFrame(
        {
            "deployment_date": ["2024-01-15T00:00:00Z"],
            "lead_time_days": [3.0],
        }
    )
    recovery_df = pd.DataFrame(
        {
            "recovery_deployment_tag": ["v1.1.0"],
            "recovery_deployment_date": ["2024-01-15T00:00:00Z"],
            "recovery_time_days": [7.0],
        }
    )

    monthly, yearly, summary = calculate_metrics(config, deployments_df, commits_df, recovery_df)

    assert set(monthly["repository_slug"]) == {"grafana"}
    assert set(yearly["repository_name"]) == {"Grafana"}
    assert summary["repository_full_name"] == "grafana/grafana"
    assert (config.results_dir / "dora_metrics_monthly.csv").exists()
    assert (config.results_dir / "dora_metrics_yearly.csv").exists()

    payload = json.loads((config.results_dir / "summary.json").read_text(encoding="utf-8"))
    assert payload["repository_slug"] == "grafana"


def test_export_combined_metrics_writes_all_repository_files(tmp_path) -> None:
    config = AppConfig(
        root_dir=tmp_path,
        data_dir=tmp_path / "data",
        raw_data_root_dir=tmp_path / "data" / "raw",
        processed_data_root_dir=tmp_path / "data" / "processed",
        results_root_dir=tmp_path / "data" / "results",
        charts_root_dir=tmp_path / "charts",
        cache_dir=tmp_path / ".cache",
    )
    combined_dir = config.results_root_dir / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)

    monthly_frames = [
        pd.DataFrame(
            {
                "repository_slug": ["appflowy"],
                "repository_name": ["AppFlowy"],
                "repository_full_name": ["AppFlowy-IO/AppFlowy"],
                "period": ["2024-01"],
                "metric_name": ["deployment_frequency"],
                "metric_value": [2],
                "metric_note": [None],
            }
        ),
        pd.DataFrame(
            {
                "repository_slug": ["keycloak"],
                "repository_name": ["Keycloak"],
                "repository_full_name": ["keycloak/keycloak"],
                "period": ["2024-01"],
                "metric_name": ["deployment_frequency"],
                "metric_value": [1],
                "metric_note": [None],
            }
        ),
    ]

    combined_monthly, combined_yearly = export_combined_metrics(config, monthly_frames, monthly_frames)

    assert len(combined_monthly) == 2
    assert len(combined_yearly) == 2
    assert (combined_dir / "dora_metrics_monthly_all_repos.csv").exists()
    assert (combined_dir / "dora_metrics_yearly_all_repos.csv").exists()


def test_build_repository_configs_defaults_to_all_supported_repositories() -> None:
    configs = build_repository_configs(AppConfig())
    assert [config.repository_slug for config in configs] == ["appflowy", "grafana", "keycloak"]
