from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dataclasses import field


class GitHubApiError(RuntimeError):
    """Raised when the GitHub API request fails."""


@dataclass
class GitHubApiClient:
    owner: str
    repo: str
    token: str | None = None
    timeout: int = 30
    api_base_url: str = "https://api.github.com"
    session: requests.Session = field(init=False)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "dora-appflowy-analyzer",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def __post_init__(self) -> None:
        # Create a session with retry/backoff to handle transient network/DNS issues
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "DELETE", "PATCH"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        self.session = session

    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip("/")
        return f"{self.api_base_url}/repos/{self.owner}/{self.repo}/{endpoint}"

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> requests.Response:
        try:
            response = self.session.get(
                self._build_url(endpoint),
                headers=self._headers(),
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise GitHubApiError(
                "Network error when contacting GitHub API. "
                "Check network/DNS/proxy settings and try again.",
            ) from exc
        self._raise_for_status(response)
        return response

    def get_paginated(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        base_params = dict(params or {})
        base_params.setdefault("per_page", 100)
        results: list[dict[str, Any]] = []
        next_url: str | None = self._build_url(endpoint)
        next_params: dict[str, Any] | None = base_params

        while next_url:
            try:
                response = self.session.get(
                    next_url,
                    headers=self._headers(),
                    params=next_params,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise GitHubApiError(
                    "Network error when contacting GitHub API while paginating. "
                    "Check network/DNS/proxy settings and try again."
                ) from exc
            self._raise_for_status(response)
            payload = response.json()
            if not isinstance(payload, list):
                raise GitHubApiError(f"Expected a list response for '{endpoint}', got: {type(payload).__name__}")
            if not payload:
                break
            results.extend(payload)
            next_link = response.links.get("next", {}).get("url")
            if not next_link:
                break
            next_url = next_link
            next_params = None

        return results

    def get_releases(self) -> list[dict[str, Any]]:
        return self.get_paginated("releases")

    def get_issues(self, *, state: str = "closed", since: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"state": state, "direction": "desc", "sort": "updated"}
        if since:
            params["since"] = since
        return self.get_paginated("issues", params=params)

    def get_pull_requests(self, *, state: str = "closed") -> list[dict[str, Any]]:
        return self.get_paginated("pulls", params={"state": state, "sort": "updated", "direction": "desc"})

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset = response.headers.get("X-RateLimit-Reset")
            if remaining == "0":
                raise GitHubApiError(
                    "GitHub API rate limit exceeded. "
                    f"X-RateLimit-Remaining={remaining}, X-RateLimit-Reset={reset}. "
                    "Set GITHUB_TOKEN in .env or rerun with --skip-api-cache-refresh if cached data exists."
                )
        if response.status_code >= 400:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise GitHubApiError(f"GitHub API request failed with status {response.status_code}: {payload}")
