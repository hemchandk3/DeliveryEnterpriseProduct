import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_session
from app.main import app
from app.models import Project, Signal


@pytest.fixture()
def client(monkeypatch):
    # StaticPool + check_same_thread=False: TestClient dispatches the
    # endpoint via anyio's worker threadpool, and SQLite's default pooling
    # for ":memory:" hands each thread its own separate in-memory database --
    # the request thread would otherwise see an empty DB with no tables.
    # StaticPool pins every checkout to the single connection created here.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # NOTE: do not `import app.models` inside this function -- it would bind
    # a local name `app` (the top-level package) that shadows the
    # module-level `app` (the FastAPI instance) for the rest of the
    # function, since Python treats any in-function assignment as local for
    # the whole function body. The `from app.models import ...` above
    # already registers the models on Base.metadata.

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = override_session

    # seed a project and a fake gateway
    db = TestSession()
    db.add(Project(id=1, organization_id=1, key="SCRUM", name="DeliveryEnterprise"))
    db.commit()
    db.close()

    import app.api.ingest as ingest_module
    from tests.fakes import FakeGitHubGateway

    monkeypatch.setattr(
        ingest_module,
        "build_github_gateway",
        lambda: FakeGitHubGateway(
            pulls=[
                {
                    "number": 1,
                    "title": "PR",
                    "state": "open",
                    "user": {"login": "alice"},
                    "created_at": "2026-07-01T10:00:00Z",
                    "updated_at": "2026-07-01T10:00:00Z",
                    "draft": False,
                    "base": {"ref": "main"},
                }
            ],
            commits=[],
        ),
    )

    yield TestClient(app), TestSession
    app.dependency_overrides.clear()


def test_ingest_github_writes_signals(client):
    test_client, TestSession = client
    resp = test_client.post(
        "/projects/1/ingest", json={"source": "github", "project_ref": "owner/repo"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"written": 1}
    db = TestSession()
    assert db.query(Signal).count() == 1
    db.close()


def test_ingest_unknown_project_returns_404(client):
    test_client, _ = client
    resp = test_client.post(
        "/projects/999/ingest", json={"source": "github", "project_ref": "owner/repo"}
    )
    assert resp.status_code == 404


def test_ingest_unknown_source_returns_400(client):
    test_client, _ = client
    resp = test_client.post(
        "/projects/1/ingest", json={"source": "slack", "project_ref": "x"}
    )
    assert resp.status_code == 400
