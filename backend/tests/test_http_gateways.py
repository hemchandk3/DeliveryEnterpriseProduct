import httpx

from app.connectors.github import GitHubHttpGateway
from app.connectors.jira import JiraHttpGateway


def test_github_gateway_lists_pulls():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/repo/pulls"
        return httpx.Response(200, json=[{"number": 1}])

    gateway = GitHubHttpGateway(token="x")
    gateway._client = httpx.Client(
        base_url="https://api.github.com", transport=httpx.MockTransport(handler)
    )

    assert gateway.list_pull_requests("owner/repo") == [{"number": 1}]


def test_github_gateway_lists_commits():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/repo/commits"
        return httpx.Response(200, json=[{"sha": "abc"}])

    gateway = GitHubHttpGateway(token="x")
    gateway._client = httpx.Client(
        base_url="https://api.github.com", transport=httpx.MockTransport(handler)
    )

    assert gateway.list_commits("owner/repo") == [{"sha": "abc"}]


def test_github_gateway_lists_pull_request_reviews():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/repo/pulls/47/reviews"
        return httpx.Response(200, json=[{"user": {"login": "dan-ohis"}, "state": "APPROVED"}])

    gateway = GitHubHttpGateway(token="x")
    gateway._client = httpx.Client(
        base_url="https://api.github.com", transport=httpx.MockTransport(handler)
    )

    reviews = gateway.list_pull_request_reviews("owner/repo", 47)
    assert reviews == [{"user": {"login": "dan-ohis"}, "state": "APPROVED"}]


def test_github_gateway_lists_requested_reviewers():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/repo/pulls/47/requested_reviewers"
        return httpx.Response(200, json={"users": [{"login": "dan-ohis"}], "teams": []})

    gateway = GitHubHttpGateway(token="x")
    gateway._client = httpx.Client(
        base_url="https://api.github.com", transport=httpx.MockTransport(handler)
    )

    payload = gateway.list_requested_reviewers("owner/repo", 47)
    assert payload == {"users": [{"login": "dan-ohis"}], "teams": []}


def test_jira_gateway_searches_issues():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/api/3/search"
        assert request.url.params["jql"] == "project=SCRUM ORDER BY updated DESC"
        return httpx.Response(200, json={"issues": [{"key": "SCRUM-42"}]})

    gateway = JiraHttpGateway(base_url="https://example.atlassian.net", email="a@b.com", token="x")
    gateway._client = httpx.Client(
        base_url="https://example.atlassian.net", transport=httpx.MockTransport(handler)
    )

    assert gateway.search_issues("SCRUM") == [{"key": "SCRUM-42"}]


def test_jira_gateway_lists_sprints_via_board_discovery():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/agile/1.0/board":
            return httpx.Response(200, json={"values": [{"id": 9}]})
        assert request.url.path == "/rest/agile/1.0/board/9/sprint"
        return httpx.Response(200, json={"values": [{"id": 3, "name": "Sprint 3"}]})

    gateway = JiraHttpGateway(base_url="https://example.atlassian.net", email="a@b.com", token="x")
    gateway._client = httpx.Client(
        base_url="https://example.atlassian.net", transport=httpx.MockTransport(handler)
    )

    assert gateway.list_sprints("SCRUM") == [{"id": 3, "name": "Sprint 3"}]


def test_jira_gateway_returns_empty_sprints_when_no_board():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"values": []})

    gateway = JiraHttpGateway(base_url="https://example.atlassian.net", email="a@b.com", token="x")
    gateway._client = httpx.Client(
        base_url="https://example.atlassian.net", transport=httpx.MockTransport(handler)
    )

    assert gateway.list_sprints("SCRUM") == []
