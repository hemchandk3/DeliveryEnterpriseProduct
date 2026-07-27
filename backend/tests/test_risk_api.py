"""API-level tests for the Detect endpoints (SCRUM-9, SCRUM-10):

    GET  /projects/{id}/sprints/{sprint_id}/health
    GET  /projects/{id}/risks
    POST /projects/{id}/risks/detect

Follows the fixture pattern in test_ingest_api.py: an in-memory
StaticPool SQLite engine shared across the TestClient's worker thread.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.connectors.github import GitHubConnector
from app.connectors.jira import JiraConnector
from app.db import Base, get_session
from app.ingest.service import IngestService
from app.main import app
from app.models import Project, Risk
from tests.fakes import FakeGitHubGateway, FakeJiraGateway
from tests.fixtures import scrum_demo_data as demo


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = override_session

    db = TestSession()
    project = Project(key=demo.PROJECT_KEY, name="DeliveryEnterprise")
    db.add(project)
    db.commit()

    service = IngestService(db)
    github_gateway = FakeGitHubGateway(
        pulls=demo.PULL_REQUESTS,
        commits=demo.COMMITS,
        reviews=demo.PR_REVIEWS,
        requested_reviewers=demo.PR_REQUESTED_REVIEWERS,
    )
    jira_gateway = FakeJiraGateway(issues=demo.ISSUES, sprints=demo.SPRINTS)
    service.run(project, GitHubConnector(github_gateway), demo.REPO)
    service.run(project, JiraConnector(jira_gateway), demo.PROJECT_KEY)
    project_id = project.id
    db.close()

    yield TestClient(app), TestSession, project_id
    app.dependency_overrides.clear()


def test_get_sprint_health_reads_green(client):
    test_client, _, project_id = client

    resp = test_client.get(f"/projects/{project_id}/sprints/3/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "green"
    assert body["issues_done"] == 9
    assert body["issues_in_progress"] == 2
    assert body["issues_todo"] == 1
    assert "burndown" in body and len(body["burndown"]) > 0
    assert "factors" in body and len(body["factors"]) > 0


def test_get_sprint_health_unknown_project_404(client):
    test_client, _, _ = client
    resp = test_client.get("/projects/999/sprints/3/health")
    assert resp.status_code == 404


def test_get_sprint_health_unknown_sprint_404(client):
    test_client, _, project_id = client
    resp = test_client.get(f"/projects/{project_id}/sprints/999/health")
    assert resp.status_code == 404


def test_detect_then_list_risks_round_trip(client):
    test_client, TestSession, project_id = client

    detect_resp = test_client.post(f"/projects/{project_id}/risks/detect")
    assert detect_resp.status_code == 200
    detected = detect_resp.json()
    assert len(detected) == 1
    assert detected[0]["target_external_id"] == "SCRUM-42"
    assert detected[0]["status"] == "AT_RISK"

    list_resp = test_client.get(f"/projects/{project_id}/risks")
    assert list_resp.status_code == 200
    listed = list_resp.json()
    assert len(listed) == 1
    assert listed[0]["target_external_id"] == "SCRUM-42"
    assert listed[0]["trigger_signal_ids"]

    db = TestSession()
    assert db.query(Risk).count() == 1
    db.close()


def test_re_detect_is_idempotent_via_api(client):
    test_client, TestSession, project_id = client

    test_client.post(f"/projects/{project_id}/risks/detect")
    test_client.post(f"/projects/{project_id}/risks/detect")

    db = TestSession()
    assert db.query(Risk).count() == 1
    db.close()


def test_list_risks_empty_before_detect(client):
    test_client, _, project_id = client
    resp = test_client.get(f"/projects/{project_id}/risks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_detect_unknown_project_404(client):
    test_client, _, _ = client
    resp = test_client.post("/projects/999/risks/detect")
    assert resp.status_code == 404
