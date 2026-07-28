from datetime import datetime
from typing import Protocol

import httpx

from app.schemas.signal import SignalIn


class GitHubGateway(Protocol):
    def list_pull_requests(self, repo: str) -> list[dict]: ...
    def list_commits(self, repo: str) -> list[dict]: ...

    # Evidence-extension (Workstream #0 §5.2): PR review/reviewer state is not
    # present on the base /pulls payload -- it requires separate calls.
    def list_pull_request_reviews(self, repo: str, number: int) -> list[dict]: ...
    def list_requested_reviewers(self, repo: str, number: int) -> dict: ...


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _normalize_reviews(reviews: list[dict]) -> list[dict]:
    return [
        {"user": (review.get("user") or {}).get("login"), "state": review.get("state")}
        for review in reviews
    ]


def _normalize_requested_reviewers(payload: dict) -> list[str]:
    return [user.get("login") for user in payload.get("users", []) if user.get("login")]


class GitHubConnector:
    source = "github"

    def __init__(self, gateway: GitHubGateway) -> None:
        self._gateway = gateway

    def fetch(self, project_ref: str) -> list[SignalIn]:
        signals: list[SignalIn] = []
        for pr in self._gateway.list_pull_requests(project_ref):
            number = pr["number"]
            reviews = _normalize_reviews(
                self._gateway.list_pull_request_reviews(project_ref, number)
            )
            requested_reviewers = _normalize_requested_reviewers(
                self._gateway.list_requested_reviewers(project_ref, number)
            )
            signals.append(
                SignalIn(
                    source=self.source,
                    kind="pr",
                    external_id=str(number),
                    title=pr.get("title"),
                    state=pr.get("state"),
                    actor=(pr.get("user") or {}).get("login"),
                    source_created_at=_dt(pr["created_at"]),
                    source_updated_at=_dt(pr["updated_at"]),
                    meta={
                        "draft": pr.get("draft", False),
                        "base_ref": (pr.get("base") or {}).get("ref"),
                        "requested_reviewers": requested_reviewers,
                        "reviews": reviews,
                    },
                )
            )
        for commit in self._gateway.list_commits(project_ref):
            info = commit["commit"]
            author_date = info["author"]["date"]
            signals.append(
                SignalIn(
                    source=self.source,
                    kind="commit",
                    external_id=commit["sha"],
                    title=info["message"].splitlines()[0],
                    state=None,
                    actor=(commit.get("author") or {}).get("login"),
                    source_created_at=_dt(author_date),
                    source_updated_at=_dt(author_date),
                    meta={},
                )
            )
        return signals


class GitHubHttpGateway:
    def __init__(self, token: str, base_url: str = "https://api.github.com") -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=30.0,
        )

    def list_pull_requests(self, repo: str) -> list[dict]:
        resp = self._client.get(f"/repos/{repo}/pulls", params={"state": "all", "per_page": 50})
        resp.raise_for_status()
        return resp.json()

    def list_commits(self, repo: str) -> list[dict]:
        resp = self._client.get(f"/repos/{repo}/commits", params={"per_page": 50})
        resp.raise_for_status()
        return resp.json()

    def list_pull_request_reviews(self, repo: str, number: int) -> list[dict]:
        resp = self._client.get(f"/repos/{repo}/pulls/{number}/reviews")
        resp.raise_for_status()
        return resp.json()

    def list_requested_reviewers(self, repo: str, number: int) -> dict:
        resp = self._client.get(f"/repos/{repo}/pulls/{number}/requested_reviewers")
        resp.raise_for_status()
        return resp.json()
