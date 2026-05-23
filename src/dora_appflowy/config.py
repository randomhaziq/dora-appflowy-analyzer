from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_ROOT_DIR = DATA_DIR / "raw"
PROCESSED_DATA_ROOT_DIR = DATA_DIR / "processed"
RESULTS_ROOT_DIR = DATA_DIR / "results"
CHARTS_ROOT_DIR = ROOT_DIR / "charts"
CACHE_DIR = ROOT_DIR / ".cache"

DEFAULT_START_DATE = os.getenv("START_DATE")
DEFAULT_END_DATE = os.getenv("END_DATE")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_INCLUDE_PRERELEASES = os.getenv("INCLUDE_PRERELEASES", "false").lower() == "true"


@dataclass(frozen=True)
class RepositoryDefinition:
    slug: str
    display_name: str
    owner: str
    repo: str
    repo_url: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


REPOSITORIES: dict[str, RepositoryDefinition] = {
    "appflowy": RepositoryDefinition(
        slug="appflowy",
        display_name="AppFlowy",
        owner="AppFlowy-IO",
        repo="AppFlowy",
        repo_url="https://github.com/AppFlowy-IO/AppFlowy.git",
    ),
    "grafana": RepositoryDefinition(
        slug="grafana",
        display_name="Grafana",
        owner="grafana",
        repo="grafana",
        repo_url="https://github.com/grafana/grafana.git",
    ),
    "keycloak": RepositoryDefinition(
        slug="keycloak",
        display_name="Keycloak",
        owner="keycloak",
        repo="keycloak",
        repo_url="https://github.com/keycloak/keycloak.git",
    ),
}


@dataclass(frozen=True)
class AppConfig:
    repository: RepositoryDefinition = REPOSITORIES["appflowy"]
    start_date: str | None = DEFAULT_START_DATE
    end_date: str | None = DEFAULT_END_DATE
    github_token: str | None = GITHUB_TOKEN
    include_prereleases: bool = DEFAULT_INCLUDE_PRERELEASES
    skip_api_cache_refresh: bool = False
    root_dir: Path = ROOT_DIR
    data_dir: Path = DATA_DIR
    raw_data_root_dir: Path = RAW_DATA_ROOT_DIR
    processed_data_root_dir: Path = PROCESSED_DATA_ROOT_DIR
    results_root_dir: Path = RESULTS_ROOT_DIR
    charts_root_dir: Path = CHARTS_ROOT_DIR
    cache_dir: Path = CACHE_DIR

    @property
    def repository_slug(self) -> str:
        return self.repository.slug

    @property
    def repository_name(self) -> str:
        return self.repository.display_name

    @property
    def repository_full_name(self) -> str:
        return self.repository.full_name

    @property
    def owner(self) -> str:
        return self.repository.owner

    @property
    def repo(self) -> str:
        return self.repository.repo

    @property
    def repo_url(self) -> str:
        return self.repository.repo_url

    @property
    def local_repo_path(self) -> Path:
        return self.cache_dir / self.repository_slug

    @property
    def raw_data_dir(self) -> Path:
        return self.raw_data_root_dir / self.repository_slug

    @property
    def processed_data_dir(self) -> Path:
        return self.processed_data_root_dir / self.repository_slug

    @property
    def results_dir(self) -> Path:
        return self.results_root_dir / self.repository_slug

    @property
    def charts_dir(self) -> Path:
        return self.charts_root_dir / self.repository_slug

    def with_overrides(
        self,
        *,
        repository: RepositoryDefinition | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        include_prereleases: bool | None = None,
        skip_api_cache_refresh: bool | None = None,
    ) -> "AppConfig":
        updated = self
        if repository is not None:
            updated = replace(updated, repository=repository)
        if start_date is not None:
            updated = replace(updated, start_date=start_date)
        if end_date is not None:
            updated = replace(updated, end_date=end_date)
        if include_prereleases is not None:
            updated = replace(updated, include_prereleases=include_prereleases)
        if skip_api_cache_refresh is not None:
            updated = replace(updated, skip_api_cache_refresh=skip_api_cache_refresh)
        return updated


def combined_results_dir(config: AppConfig) -> Path:
    return config.results_root_dir / "combined"


def combined_charts_dir(config: AppConfig) -> Path:
    return config.charts_root_dir / "combined"


def ensure_directories(config: AppConfig) -> None:
    for path in (
        config.cache_dir,
        config.raw_data_root_dir,
        config.processed_data_root_dir,
        config.results_root_dir,
        config.charts_root_dir,
        config.local_repo_path.parent,
        config.raw_data_dir,
        config.processed_data_dir,
        config.results_dir,
        config.charts_dir,
        combined_results_dir(config),
        combined_charts_dir(config),
    ):
        path.mkdir(parents=True, exist_ok=True)


def get_repository(slug: str) -> RepositoryDefinition:
    try:
        return REPOSITORIES[slug]
    except KeyError as exc:
        supported = ", ".join(sorted(REPOSITORIES))
        raise ValueError(f"Unsupported repository '{slug}'. Supported repositories: {supported}") from exc


def build_repository_configs(base_config: AppConfig, repository_slugs: list[str] | None = None) -> list[AppConfig]:
    selected_slugs = repository_slugs or list(REPOSITORIES)
    return [base_config.with_overrides(repository=get_repository(slug)) for slug in selected_slugs]
