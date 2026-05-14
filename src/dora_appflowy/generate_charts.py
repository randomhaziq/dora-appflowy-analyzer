from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .config import AppConfig


def _save_line_chart(series_df: pd.DataFrame, title: str, ylabel: str, output_path) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(series_df["period"], series_df["metric_value"], marker="o")
    plt.title(title)
    plt.xlabel("Period")
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def generate_charts(config: AppConfig, monthly_metrics: pd.DataFrame, yearly_metrics: pd.DataFrame) -> None:
    monthly_chart_specs = [
        ("deployment_frequency", "Deployment Frequency by Month", "Deployments", config.charts_dir / "deployment_frequency_monthly.png"),
        ("lead_time_days_mean", "Lead Time for Changes by Month", "Days", config.charts_dir / "lead_time_monthly.png"),
        ("recovery_time_days_mean", "Mean Time to Recover by Month", "Days", config.charts_dir / "mttr_monthly.png"),
        ("adapted_bugfix_deployment_rate", "Adapted Bugfix Deployment Rate by Month", "Rate", config.charts_dir / "adapted_cfr_monthly.png"),
    ]
    yearly_chart_specs = [
        ("deployment_frequency", "Deployment Frequency by Year", "Deployments", config.charts_dir / "deployment_frequency_yearly.png"),
        ("lead_time_days_mean", "Lead Time for Changes by Year", "Days", config.charts_dir / "lead_time_yearly.png"),
        ("recovery_time_days_mean", "Mean Time to Recover by Year", "Days", config.charts_dir / "mttr_yearly.png"),
        ("adapted_bugfix_deployment_rate", "Adapted Bugfix Deployment Rate by Year", "Rate", config.charts_dir / "adapted_cfr_yearly.png"),
    ]

    for metric_name, title, ylabel, path in monthly_chart_specs:
        metric_df = monthly_metrics[monthly_metrics["metric_name"] == metric_name].copy()
        if metric_df.empty:
            continue
        _save_line_chart(metric_df, title, ylabel, path)

    for metric_name, title, ylabel, path in yearly_chart_specs:
        metric_df = yearly_metrics[yearly_metrics["metric_name"] == metric_name].copy()
        if metric_df.empty:
            continue
        _save_line_chart(metric_df, title, ylabel, path)
