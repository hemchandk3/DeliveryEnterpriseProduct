"""Persists Detect-stage findings as `Risk` rows (SCRUM-10).

Upserts on the ORM's unique `(project_id, risk_type, target_external_id)`
constraint (app/models/risk.py) so re-running detection is idempotent --
a repeat detect updates the existing row's evidence rather than
duplicating it.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.risk import Risk
from app.risk.schemas import RiskFinding


def persist_findings(session: Session, project_id: int, findings: list[RiskFinding]) -> list[Risk]:
    persisted = [_upsert(session, project_id, finding) for finding in findings]
    session.commit()
    return persisted


def _upsert(session: Session, project_id: int, finding: RiskFinding) -> Risk:
    stmt = select(Risk).where(
        Risk.project_id == project_id,
        Risk.risk_type == finding.risk_type,
        Risk.target_external_id == finding.target_external_id,
    )
    existing = session.scalars(stmt).one_or_none()
    if existing is None:
        risk = Risk(
            project_id=project_id,
            risk_type=finding.risk_type,
            target_external_id=finding.target_external_id,
            severity=finding.severity,
            confidence=finding.confidence,
            status=finding.status,
            reasons=finding.reasons,
            trigger_signal_ids=finding.trigger_signal_ids,
        )
        session.add(risk)
        return risk

    existing.severity = finding.severity
    existing.confidence = finding.confidence
    existing.status = finding.status
    existing.reasons = finding.reasons
    existing.trigger_signal_ids = finding.trigger_signal_ids
    existing.detected_at = datetime.now(UTC)
    return existing
