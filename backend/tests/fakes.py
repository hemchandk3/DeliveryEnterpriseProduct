class FakeGitHubGateway:
    """In-memory GitHubGateway used by connector/unit tests -- no network.

    ``reviews`` and ``requested_reviewers`` are keyed by PR number, mirroring
    the real GitHub API where those live behind separate endpoints
    (``/pulls/{n}/reviews`` and ``/pulls/{n}/requested_reviewers``).
    """

    def __init__(
        self,
        pulls: list[dict],
        commits: list[dict],
        reviews: dict[int, list[dict]] | None = None,
        requested_reviewers: dict[int, list[dict]] | None = None,
    ) -> None:
        self._pulls = pulls
        self._commits = commits
        self._reviews = reviews or {}
        self._requested_reviewers = requested_reviewers or {}

    def list_pull_requests(self, repo: str) -> list[dict]:
        return self._pulls

    def list_commits(self, repo: str) -> list[dict]:
        return self._commits

    def list_pull_request_reviews(self, repo: str, number: int) -> list[dict]:
        return self._reviews.get(number, [])

    def list_requested_reviewers(self, repo: str, number: int) -> dict:
        return {"users": self._requested_reviewers.get(number, []), "teams": []}


class FakeJiraGateway:
    def __init__(self, issues: list[dict], sprints: list[dict]) -> None:
        self._issues = issues
        self._sprints = sprints

    def search_issues(self, project_key: str) -> list[dict]:
        return self._issues

    def list_sprints(self, project_key: str) -> list[dict]:
        return self._sprints
