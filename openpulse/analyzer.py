"""Transform GitHub API responses into a compact repository report."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from statistics import median

from .github_api import GitHubClient


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _age_days(value: str | None, now: datetime) -> int | None:
    created = _parse_date(value)
    return max(0, (now - created).days) if created else None


def _clean_repo_name(value: str) -> tuple[str, str]:
    value = value.strip().removeprefix("https://github.com/").strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value):
        raise ValueError("Enter a valid repository as owner/repo.")
    owner, repo = value.split("/", 1)
    return owner, repo.removesuffix(".git")


def _issue_record(item: dict, now: datetime) -> dict:
    return {
        "number": item.get("number"),
        "title": item.get("title") or "(untitled)",
        "age_days": _age_days(item.get("created_at"), now),
        "labels": ", ".join(label.get("name", "") for label in item.get("labels", [])),
        "author": (item.get("user") or {}).get("login", "unknown"),
        "url": item.get("html_url", ""),
    }


def analyze_repository(client: GitHubClient, repo_name: str, commit_limit: int = 30) -> dict:
    owner, name = _clean_repo_name(repo_name)
    now = datetime.now(timezone.utc)
    repository = client.get_repository(owner, name)
    commits = client.list_commits(owner, name, commit_limit)
    issues = client.list_open_issues(owner, name)
    pull_requests = client.list_open_pull_requests(owner, name)

    recent_commits, authors, activity = [], set(), {}
    for item in commits:
        commit_data = item.get("commit") or {}
        author_data = commit_data.get("author") or {}
        date = _parse_date(author_data.get("date"))
        author = ((item.get("author") or {}).get("login")
                  or author_data.get("name") or "unknown")
        if author != "unknown":
            authors.add(author)
        recent_commits.append({
            "sha": (item.get("sha") or "")[:7],
            "message": (commit_data.get("message") or "").splitlines()[0],
            "author": author,
            "date": date.date().isoformat() if date else "unknown",
        })
        if date:
            key = date.date().isoformat()
            activity[key] = activity.get(key, 0) + 1

    issue_records = [_issue_record(item, now) for item in issues]
    pr_records = [_issue_record(item, now) for item in pull_requests]
    issue_ages = [r["age_days"] for r in issue_records if r["age_days"] is not None]
    pr_ages = [r["age_days"] for r in pr_records if r["age_days"] is not None]

    return {
        "generated_at": now.isoformat(),
        "repository": {
            "full_name": repository.get("full_name", f"{owner}/{name}"),
            "name": repository.get("name", name),
            "description": repository.get("description"),
            "html_url": repository.get("html_url", f"https://github.com/{owner}/{name}"),
            "stargazers_count": repository.get("stargazers_count", 0),
            "forks_count": repository.get("forks_count", 0),
            "open_issues_count": repository.get("open_issues_count", 0),
            "default_branch": repository.get("default_branch", "main"),
            "license": (repository.get("license") or {}).get("spdx_id"),
            "created_at": repository.get("created_at"),
            "updated_at": repository.get("updated_at"),
        },
        "metrics": {
            "open_issues": len(issue_records),
            "open_pull_requests": len(pr_records),
            "recent_commit_count": len(recent_commits),
            "contributor_count": len(authors),
            "median_open_issue_age_days": round(median(issue_ages)) if issue_ages else None,
            "median_open_pr_age_days": round(median(pr_ages)) if pr_ages else None,
        },
        "commit_activity": [{"date": day, "commits": activity[day]} for day in sorted(activity)],
        "recent_commits": recent_commits,
        "open_issues": issue_records,
        "open_pull_requests": pr_records,
    }
