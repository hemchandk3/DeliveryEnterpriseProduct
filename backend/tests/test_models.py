from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Project, Signal


def _signal(project_id: int, external_id: str = "1") -> Signal:
    now = datetime(2026, 7, 1, tzinfo=UTC)
    return Signal(
        project_id=project_id,
        source="github",
        kind="pr",
        external_id=external_id,
        title="Add login",
        state="open",
        actor="alice",
        source_created_at=now,
        source_updated_at=now,
        meta={"additions": 10},
    )


def test_signal_persists_and_reads_back(session):
    project = Project(key="SCRUM", name="DeliveryEnterprise")
    session.add(project)
    session.commit()

    session.add(_signal(project.id))
    session.commit()

    stored = session.query(Signal).one()
    assert stored.source == "github"
    assert stored.meta == {"additions": 10}
    assert stored.ingested_at is not None


def test_signal_identity_is_unique(session):
    project = Project(key="SCRUM", name="DeliveryEnterprise")
    session.add(project)
    session.commit()

    session.add(_signal(project.id, external_id="7"))
    session.commit()
    session.add(_signal(project.id, external_id="7"))
    with pytest.raises(IntegrityError):
        session.commit()
