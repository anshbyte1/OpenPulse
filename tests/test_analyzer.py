from datetime import datetime, timezone

import pytest

from openpulse.analyzer import _age_days, _clean_repo_name, analyze_repository


def test_clean_repo_name_accepts_url_and_slug():
    assert _clean_repo_name("https://github.com/pallets/flask") == ("pallets", "flask")
    assert _clean_repo_name("psf/requests.git") == ("psf", "requests")


@pytest.mark.parametrize("value", ["", "owner", "https://gitlab.com/a/b", "a/b/c", "bad name/repo"])
def test_clean_repo_name_rejects_invalid_input(value):
    with pytest.raises(ValueError):
        _clean_repo_name(value)


def test_age_days():
    now = datetime(2025, 1, 10, tzinfo=timezone.utc)
    assert _age_days("2025-01-07T00:00:00Z", now) == 3
    assert _age_days(None, now) is None


class FakeClient:
    def get_repository(self, owner, repo):
        return {"full_name": f"{owner}/{repo}", "name": repo, "stargazers_count": 12,
                "forks_count": 3, "open_issues_count": 1, "html_url": "https://github.com/x/y"}

    def list_commits(self, owner, repo, limit):
        return [{"sha": "abcdef123", "commit": {"message": "Fix bug\nDetails",
                "author": {"name": "Dev", "date": "2025-01-09T10:00:00Z"}},
                "author": {"login": "dev"}}]

    def list_open_issues(self, owner, repo, limit=100):
        return [{"number": 1, "title": "Bug", "created_at": "2025-01-08T00:00:00Z",
                 "labels": [{"name": "bug"}], "user": {"login": "reporter"},
                 "html_url": "https://github.com/x/y/issues/1"}]

    def list_open_pull_requests(self, owner, repo, limit=100):
        return []


def test_analyze_repository_builds_expected_shape():
    report = analyze_repository(FakeClient(), "x/y")
    assert report["repository"]["full_name"] == "x/y"
    assert report["metrics"]["recent_commit_count"] == 1
    assert report["metrics"]["contributor_count"] == 1
    assert report["open_issues"][0]["labels"] == "bug"
    assert report["commit_activity"][0]["commits"] == 1
