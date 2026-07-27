"""StalledCriticalStoryDetector against the curated demo dataset (SCRUM-10).

Drives AC-DETECT's risk half end-to-end: ingest the real fixture, run the
detector, and assert exactly SCRUM-42 is flagged with zero false positives
across the 9 Done stories, SCRUM-45, and SCRUM-51 (SCRUM-10 acceptance
criteria).
"""

from datetime import UTC, datetime

import pytest

from app.models.signal import Signal
from app.risk.audit import AuditSink
from app.risk.detectors import StalledCriticalStoryDetector
from tests.fixtures import load_demo_dataset

DEMO_NOW = datetime(2026, 7, 24, tzinfo=UTC)


@pytest.fixture()
def demo_project(session):
    return load_demo_dataset(session)


def test_exactly_scrum_42_is_flagged(session, demo_project):
    findings = StalledCriticalStoryDetector().detect(session, demo_project.id, DEMO_NOW)

    assert [f.target_external_id for f in findings] == ["SCRUM-42"]
    assert findings[0].status == "AT_RISK"
    assert findings[0].risk_type == "stalled_critical_story"


def test_no_false_positives_on_healthy_or_todo_stories(session, demo_project):
    findings = StalledCriticalStoryDetector().detect(session, demo_project.id, DEMO_NOW)
    flagged = {f.target_external_id for f in findings}

    done_stories = {"SCRUM-40", "SCRUM-41", "SCRUM-43", "SCRUM-44", "SCRUM-46",
                    "SCRUM-47", "SCRUM-48", "SCRUM-49", "SCRUM-50"}
    assert not (flagged & done_stories)
    assert "SCRUM-45" not in flagged  # In Progress but not stale (updated 2026-07-22)
    assert "SCRUM-51" not in flagged  # To Do, never evaluated


def test_finding_stores_triggering_signal_ids(session, demo_project):
    finding = StalledCriticalStoryDetector().detect(session, demo_project.id, DEMO_NOW)[0]

    assert len(finding.trigger_signal_ids) >= 2
    stmt_ids = set(finding.trigger_signal_ids)
    stored = (
        session.query(Signal)
        .filter(Signal.id.in_(stmt_ids))
        .all()
    )
    # Every trigger id resolves to a real stored Signal for this project.
    assert len(stored) == len(stmt_ids)
    assert all(s.project_id == demo_project.id for s in stored)
    # Must include the stale issue itself and the starved PR.
    kinds = {(s.kind, s.external_id) for s in stored}
    assert ("issue", "SCRUM-42") in kinds
    assert ("pr", "47") in kinds


def test_finding_names_release_gating_reasons_and_blocked_by(session, demo_project):
    finding = StalledCriticalStoryDetector().detect(session, demo_project.id, DEMO_NOW)[0]
    reasons_text = " | ".join(finding.reasons)

    assert "Highest" in reasons_text
    assert "critical-path" in reasons_text
    assert "8pts" in reasons_text
    assert "blocked by SCRUM-45" in reasons_text
    # Core detection signals: stale status + PR review starvation.
    assert "In Progress" in reasons_text
    assert "PR #47" in reasons_text
    assert "release/1.4" in reasons_text


def test_finding_has_severity_and_confidence(session, demo_project):
    finding = StalledCriticalStoryDetector().detect(session, demo_project.id, DEMO_NOW)[0]

    assert finding.severity in {"medium", "high"}
    assert 0.0 < finding.confidence <= 1.0


def test_detection_calls_audit_sink(session, demo_project):
    calls = []

    class RecordingAuditSink:
        def record_detection(self, *, project_id, risk_type, findings_count, now):
            calls.append((project_id, risk_type, findings_count, now))

    detector = StalledCriticalStoryDetector(audit=RecordingAuditSink())
    findings = detector.detect(session, demo_project.id, DEMO_NOW)

    assert calls == [(demo_project.id, "stalled_critical_story", len(findings), DEMO_NOW)]


def test_detect_with_no_matching_issues_returns_empty_list(session):
    from app.models import Project

    empty_project = Project(key="EMPTY", name="Empty")
    session.add(empty_project)
    session.commit()

    findings = StalledCriticalStoryDetector().detect(session, empty_project.id, DEMO_NOW)
    assert findings == []


def test_null_audit_sink_is_a_no_op():
    from app.risk.audit import NullAuditSink

    sink: AuditSink = NullAuditSink()
    # Must not raise.
    sink.record_detection(project_id=1, risk_type="x", findings_count=0, now=DEMO_NOW)
