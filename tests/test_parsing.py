from dora_appflowy.collect_issues import has_excluded_label, is_bug_issue
from dora_appflowy.git_utils import is_semver_like_tag
from dora_appflowy.github_api import GitHubApiClient


def test_semver_tag_detection() -> None:
    assert is_semver_like_tag("v0.7.0")
    assert is_semver_like_tag("0.7.0")
    assert is_semver_like_tag("v1.2.3-beta.1")
    assert not is_semver_like_tag("release-2024")


def test_bug_label_detection() -> None:
    assert is_bug_issue(["bug"])
    assert is_bug_issue(["type:bug"])
    assert is_bug_issue(["confirmed bug"])
    assert not is_bug_issue(["enhancement"])


def test_excluded_label_detection() -> None:
    assert has_excluded_label(["duplicate"])
    assert has_excluded_label(["not planned"])
    assert not has_excluded_label(["bug"])


def test_paginated_requests_follow_link_headers_without_page_numbers(monkeypatch) -> None:
    client = GitHubApiClient(owner="example", repo="demo")
    calls: list[tuple[str, object]] = []

    class FakeResponse:
        def __init__(self, payload, links):
            self._payload = payload
            self.links = links
            self.status_code = 200
            self.headers = {}

        def json(self):
            return self._payload

    responses = [
        FakeResponse(
            [{"id": 1}],
            {"next": {"url": "https://api.github.com/repos/example/demo/issues?after=cursor1"}},
        ),
        FakeResponse([{"id": 2}], {}),
    ]

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append((url, params))
        return responses.pop(0)

    monkeypatch.setattr("requests.get", fake_get)

    results = client.get_paginated("issues", params={"state": "closed"})

    assert results == [{"id": 1}, {"id": 2}]
    assert calls[0][1] == {"state": "closed", "per_page": 100}
    assert "page" not in calls[0][1]
    assert calls[1][0].endswith("after=cursor1")
    assert calls[1][1] is None
