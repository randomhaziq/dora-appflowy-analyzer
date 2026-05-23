from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .config import AppConfig, combined_charts_dir

MetricSpec = tuple[str, str, str, str]


def chart_specs() -> list[MetricSpec]:
    return [
        ("deployment_frequency", "Deployment Frequency", "Deployments", "deployment_frequency"),
        ("lead_time_days_mean", "Lead Time for Changes", "Days", "lead_time"),
        ("recovery_time_days_mean", "Mean Time to Recover", "Days", "mttr"),
        ("adapted_bugfix_deployment_rate", "Adapted Bugfix Deployment Rate", "Rate", "adapted_cfr"),
    ]


def _save_line_chart(series_df: pd.DataFrame, title: str, ylabel: str, output_path: Path) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(series_df["period"], series_df["metric_value"], marker="o")
    plt.title(title)
    plt.xlabel("Period")
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def _save_comparison_chart(series_df: pd.DataFrame, title: str, ylabel: str, output_path: Path) -> None:
    plt.figure(figsize=(11, 6))
    for repository_name, group in series_df.groupby("repository_name"):
        ordered = group.sort_values("period")
        plt.plot(ordered["period"], ordered["metric_value"], marker="o", label=repository_name)
    plt.title(title)
    plt.xlabel("Period")
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def generate_charts(config: AppConfig, monthly_metrics: pd.DataFrame, yearly_metrics: pd.DataFrame) -> None:
    for metric_name, chart_title, ylabel, file_slug in chart_specs():
        monthly_df = monthly_metrics[monthly_metrics["metric_name"] == metric_name].copy()
        if not monthly_df.empty:
            _save_line_chart(
                monthly_df,
                f"{config.repository_name} - {chart_title} by Month",
                ylabel,
                config.charts_dir / f"{file_slug}_monthly.png",
            )

        yearly_df = yearly_metrics[yearly_metrics["metric_name"] == metric_name].copy()
        if not yearly_df.empty:
            _save_line_chart(
                yearly_df,
                f"{config.repository_name} - {chart_title} by Year",
                ylabel,
                config.charts_dir / f"{file_slug}_yearly.png",
            )


def generate_comparison_charts(
    config: AppConfig,
    monthly_metrics: pd.DataFrame,
    yearly_metrics: pd.DataFrame,
) -> None:
    output_dir = combined_charts_dir(config)
    repository_names = " vs ".join(sorted(monthly_metrics["repository_name"].dropna().unique())) if not monthly_metrics.empty else ""

    for metric_name, chart_title, ylabel, file_slug in chart_specs():
        monthly_df = monthly_metrics[monthly_metrics["metric_name"] == metric_name].copy()
        if not monthly_df.empty:
            _save_comparison_chart(
                monthly_df,
                f"{chart_title} by Month - {repository_names}",
                ylabel,
                output_dir / f"{file_slug}_monthly_comparison.png",
            )

        yearly_df = yearly_metrics[yearly_metrics["metric_name"] == metric_name].copy()
        if not yearly_df.empty:
            names = " vs ".join(sorted(yearly_df["repository_name"].dropna().unique()))
            _save_comparison_chart(
                yearly_df,
                f"{chart_title} by Year - {names}",
                ylabel,
                output_dir / f"{file_slug}_yearly_comparison.png",
            )
