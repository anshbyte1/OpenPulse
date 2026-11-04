"""Small client for the GitHub REST API."""
from __future__ import annotations

import requests


class GitHubAPIError(RuntimeError):
    """Raised when GitHub returns an error or a request cannot be completed."""


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None, timeout: int = 15) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "OpenPulse/0.1",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: dict | None = None):
        try:
            response = self.session.get(f"{self.BASE_URL}{path}", params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise GitHubAPIError(f"GitHub request failed: {exc}") from exc
        if response.status_code == 404:
            raise GitHubAPIError("Repository or resource not found. Check the owner/repo name.")
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            reset = response.headers.get("X-RateLimit-Reset")
            suffix = f" Try again after Unix time {reset}." if reset else ""
            raise GitHubAPIError("GitHub API rate limit reached." + suffix)
        if not response.ok:
            try:
                detail = response.json().get("message", response.reason)
            except ValueError:
                detail = response.reason
            raise GitHubAPIError(f"GitHub API error ({response.status_code}): {detail}")
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned an invalid JSON response.") from exc

    def get_repository(self, owner: str, repo: str) -> dict:
        return self._get(f"/repos/{owner}/{repo}")

    def list_commits(self, owner: str, repo: str, limit: int = 30) -> list[dict]:
        return self._get(f"/repos/{owner}/{repo}/commits", {"per_page": min(limit, 100)})

    def list_open_issues(self, owner: str, repo: str, limit: int = 100) -> list[dict]:
        items = self._get(f"/repos/{owner}/{repo}/issues", {
            "state": "open", "per_page": min(limit, 100), "sort": "created", "direction": "asc"
        })
        return [item for item in items if "pull_request" not in item]

    def list_open_pull_requests(self, owner: str, repo: str, limit: int = 100) -> list[dict]:
        return self._get(f"/repos/{owner}/{repo}/pulls", {
            "state": "open", "per_page": min(limit, 100), "sort": "created", "direction": "asc"
        })
