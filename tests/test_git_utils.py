from __future__ import annotations

from pathlib import Path

import pytest

from dora_appflowy.git_utils import clone_or_update_repository


def test_clone_or_update_repository_reclones_invalid_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_path = tmp_path / ".cache" / "keycloak"
    cache_path.mkdir(parents=True)
    (cache_path / "partial.txt").write_text("incomplete clone", encoding="utf-8")

    clone_calls: list[tuple[str, Path]] = []
    sentinel_repo = object()

    def fake_clone_from(repo_url: str, local_path: Path) -> object:
        clone_calls.append((repo_url, local_path))
        local_path.mkdir(parents=True, exist_ok=True)
        (local_path / ".git").mkdir()
        return sentinel_repo

    monkeypatch.setattr("dora_appflowy.git_utils.Repo.clone_from", fake_clone_from)

    repo = clone_or_update_repository("https://example.com/keycloak.git", cache_path)

    assert repo is sentinel_repo
    assert clone_calls == [("https://example.com/keycloak.git", cache_path)]
    assert (cache_path / ".git").exists()
    assert not (cache_path / "partial.txt").exists()
