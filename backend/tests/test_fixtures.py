"""Sanity checks that the committed demo fixture (tests/fixtures/scrum_demo_data.py)
is shaped correctly for the connectors, and that ingesting it produces the
SCRUM-42 evidence trail Plan 2 (Detect) will need to score against.
"""

from app.connectors.github import GitHubConnector
from app.connectors.jira import JiraConnector
from app.ingest.service import IngestService
from app.models import Project
from tests.fakes import FakeGitHubGateway, FakeJiraGateway
from tests.fixtures import scrum_demo_data as demo


def test_github_connector_normalizes_full_fixture():
    gateway = FakeGitHubGateway(
        pulls=demo.PULL_REQUESTS,
        commits=demo.COMMITS,
        reviews=demo.PR_REVIEWS,
        requested_reviewers=demo.PR_REQUESTED_REVIEWERS,
    )

    signals = GitHubConnector(gateway).fetch(demo.REPO)

    assert len(signals) == len(demo.PULL_REQUESTS) + len(demo.COMMITS)
    pr_47 = next(s for s in signals if s.kind == "pr" and s.external_id == "47")
    assert pr_47.meta["base_ref"] == "release/1.4"
    assert pr_47.meta["requested_reviewers"] == ["dan-ohis"]
    assert pr_47.meta["reviews"] == []  # zero approvals -- the anomaly


def test_jira_connector_normalizes_full_fixture():
    gateway = FakeJiraGateway(issues=demo.ISSUES, sprints=demo.SPRINTS)

    signals = JiraConnector(gateway).fetch(demo.PROJECT_KEY)

    assert len([s for s in signals if s.kind == "issue"]) == len(demo.ISSUES)
    assert len([s for s in signals if s.kind == "sprint"]) == 1
    scrum_42 = next(s for s in signals if s.external_id == "SCRUM-42")
    assert scrum_42.state == "In Progress"
    assert scrum_42.meta["priority"] == "Highest"
    assert scrum_42.meta["story_points"] == 8
    assert scrum_42.meta["issuelinks"][0]["key"] == "SCRUM-45"


def test_ingesting_the_demo_fixture_persists_scrum_42_evidence(session):
    project = Project(organization_id=1, key=demo.PROJECT_KEY, name="DeliveryEnterprise")
    session.add(project)
    session.commit()

    service = IngestService(session)
    github_gateway = FakeGitHubGateway(
        pulls=demo.PULL_REQUESTS,
        commits=demo.COMMITS,
        reviews=demo.PR_REVIEWS,
        requested_reviewers=demo.PR_REQUESTED_REVIEWERS,
    )
    service.run(project, GitHubConnector(github_gateway), demo.REPO)

    jira_gateway = FakeJiraGateway(issues=demo.ISSUES, sprints=demo.SPRINTS)
    service.run(project, JiraConnector(jira_gateway), demo.PROJECT_KEY)

    from app.models import Signal

    scrum_42 = (
        session.query(Signal)
        .filter(Signal.external_id == "SCRUM-42", Signal.kind == "issue")
        .one()
    )
    assert scrum_42.state == "In Progress"
    assert scrum_42.meta["issuelinks"][0]["key"] == "SCRUM-45"

    pr_47 = (
        session.query(Signal)
        .filter(Signal.external_id == "47", Signal.kind == "pr")
        .one()
    )
    assert pr_47.meta["base_ref"] == "release/1.4"
    assert pr_47.meta["reviews"] == []
