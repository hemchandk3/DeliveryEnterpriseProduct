"""Risk-row persistence and re-detect idempotency (SCRUM-10)."""

from datetime import UTC, datetime

import pytest

from app.models.risk import Risk
from app.risk.detectors import StalledCriticalStoryDetector
from app.risk.persistence import persist_findings
from tests.fixtures import load_demo_dataset

DEMO_NOW = datetime(2026, 7, 24, tzinfo=UTC)


@pytest.fixture()
def demo_project(session):
    return load_demo_dataset(session)


def test_persist_findings_writes_one_risk_row(session, demo_project):
    findings = StalledCriticalStoryDetector().detect(session, demo_project.id, DEMO_NOW)

    persist_findings(session, demo_project.id, findings)

    stored = session.query(Risk).all()
    assert len(stored) == 1
    assert stored[0].target_external_id == "SCRUM-42"
    assert stored[0].trigger_signal_ids == findings[0].trigger_signal_ids
    assert stored[0].reasons == findings[0].reasons


def test_re_detect_is_idempotent_upsert_not_duplicate(session, demo_project):
    detector = StalledCriticalStoryDetector()

    findings_1 = detector.detect(session, demo_project.id, DEMO_NOW)
    persist_findings(session, demo_project.id, findings_1)

    findings_2 = detector.detect(session, demo_project.id, DEMO_NOW)
    persist_findings(session, demo_project.id, findings_2)

    assert session.query(Risk).count() == 1
