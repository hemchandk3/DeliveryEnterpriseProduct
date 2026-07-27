"""Test-only helpers for loading the curated demo dataset (scrum_demo_data)
into a fresh in-memory session via the real connectors + IngestService --
i.e. the same path live data takes, per docs/ENGINEERING_STANDARDS.md
("fixtures are for deterministic tests only, never a substitute for
real-data verification of the feature itself"). Used by Detect-stage tests
(test_sprint_health.py, test_detectors.py, test_risk_api.py) that need a
fully ingested Signal store to score/detect against.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.connectors.github import GitHubConnector
from app.connectors.jira import JiraConnector
from app.ingest.service import IngestService
from app.models import Project
from tests.fakes import FakeGitHubGateway, FakeJiraGateway
from tests.fixtures import scrum_demo_data as demo


def load_demo_dataset(session: Session) -> Project:
    """Ingest the full curated SCRUM/DeliveryEnterprise dataset and return
    the persisted `Project`."""
    project = Project(key=demo.PROJECT_KEY, name="DeliveryEnterprise")
    session.add(project)
    session.commit()

    service = IngestService(session)
    github_gateway = FakeGitHubGateway(
        pulls=demo.PULL_REQUESTS,
        commits=demo.COMMITS,
        reviews=demo.PR_REVIEWS,
        requested_reviewers=demo.PR_REQUESTED_REVIEWERS,
    )
    jira_gateway = FakeJiraGateway(issues=demo.ISSUES, sprints=demo.SPRINTS)

    service.run(project, GitHubConnector(github_gateway), demo.REPO)
    service.run(project, JiraConnector(jira_gateway), demo.PROJECT_KEY)

    return project
