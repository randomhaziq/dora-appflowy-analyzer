from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

SEMVER_TAG_PATTERN = re.compile(r"^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def is_semver_like_tag(tag_name: str) -> bool:
    return bool(SEMVER_TAG_PATTERN.fullmatch(tag_name.strip()))


def clone_or_update_repository(repo_url: str, local_path: Path) -> Repo:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if not local_path.exists():
        try:
            return Repo.clone_from(repo_url, local_path)
        except GitCommandError as exc:
            raise RuntimeError(
                f"Failed to clone repository from {repo_url}. "
                "If you are offline or GitHub access is blocked, rerun in an environment with network access "
                "or pre-populate the local cache directory first."
            ) from exc

    try:
        repo = Repo(local_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        shutil.rmtree(local_path, ignore_errors=True)
        try:
            return Repo.clone_from(repo_url, local_path)
        except GitCommandError as exc:
            raise RuntimeError(
                f"Failed to refresh the invalid cached repository at {local_path} from {repo_url}. "
                "If you are offline or GitHub access is blocked, rerun in an environment with network access."
            ) from exc

    try:
        origin = repo.remotes.origin
        origin.fetch(prune=True, tags=True)
    except GitCommandError as exc:
        raise RuntimeError(
            f"Failed to fetch updates for the cached repository at {local_path}. "
            "You can still continue later once network access is available."
        ) from exc
    return repo


def get_repo(local_path: Path) -> Repo:
    if not local_path.exists():
        raise FileNotFoundError(f"Local repository not found at {local_path}")
    return Repo(local_path)


def iter_tags_sorted_by_commit_time(repo: Repo) -> list[tuple[str, object]]:
    tagged = []
    for tag in repo.tags:
        commit = tag.commit
        tagged.append((tag.name, commit))
    return sorted(tagged, key=lambda item: item[1].committed_datetime)


def commit_is_ancestor(repo_path: Path, ancestor_sha: str, descendant_ref: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_ref],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0
