from app.connectors.github import GitHubConnector
from app.ingest.service import IngestService
from app.models import Project, Signal
from tests.fakes import FakeGitHubGateway

PULL = {
    "number": 42,
    "title": "Add login",
    "state": "open",
    "user": {"login": "alice"},
    "created_at": "2026-07-01T10:00:00Z",
    "updated_at": "2026-07-02T10:00:00Z",
    "draft": False,
    "base": {"ref": "main"},
}


def _project(session) -> Project:
    project = Project(organization_id=1, key="SCRUM", name="DeliveryEnterprise")
    session.add(project)
    session.commit()
    return project


def test_run_inserts_signals(session):
    project = _project(session)
    connector = GitHubConnector(FakeGitHubGateway(pulls=[PULL], commits=[]))

    written = IngestService(session).run(project, connector, "owner/repo")

    assert written == 1
    assert session.query(Signal).count() == 1


def test_run_is_idempotent_and_updates(session):
    project = _project(session)
    updated_pull = {**PULL, "state": "closed", "updated_at": "2026-07-03T10:00:00Z"}

    IngestService(session).run(
        project, GitHubConnector(FakeGitHubGateway(pulls=[PULL], commits=[])), "owner/repo"
    )
    IngestService(session).run(
        project,
        GitHubConnector(FakeGitHubGateway(pulls=[updated_pull], commits=[])),
        "owner/repo",
    )

    assert session.query(Signal).count() == 1
    stored = session.query(Signal).one()
    assert stored.state == "closed"


def test_run_preserves_pr_evidence_meta(session):
    project = _project(session)
    pull = {**PULL, "number": 47, "base": {"ref": "release/1.4"}}
    connector = GitHubConnector(
        FakeGitHubGateway(
            pulls=[pull],
            commits=[],
            reviews={47: []},
            requested_reviewers={47: [{"login": "dan-ohis"}]},
        )
    )

    IngestService(session).run(project, connector, "owner/repo")

    stored = session.query(Signal).one()
    assert stored.meta["base_ref"] == "release/1.4"
    assert stored.meta["requested_reviewers"] == ["dan-ohis"]
    assert stored.meta["reviews"] == []
