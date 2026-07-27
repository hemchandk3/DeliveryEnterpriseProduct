"""Detect-stage API (SCRUM-9, SCRUM-10). See ARCHITECTURE.md §5.6.

    GET  /projects/{id}/sprints/{sprint_id}/health  -> SprintHealth
    GET  /projects/{id}/risks                       -> list[RiskFinding]
    POST /projects/{id}/risks/detect                -> list[RiskFinding]

`now` is optional on the scoring/detection routes and defaults to the
demo-reproducible `app.risk.config.DEMO_NOW` (2026-07-24) when omitted --
see that module's docstring. A real caller (the loop runner, SCRUM-18)
passes the current time explicitly.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Project
from app.models.risk import Risk
from app.risk.config import DEMO_NOW
from app.risk.detectors import StalledCriticalStoryDetector
from app.risk.persistence import persist_findings
from app.risk.schemas import RiskFinding, SprintHealth
from app.risk.sprint_health import score_sprint_health

router = APIRouter()


def _get_project(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects/{project_id}/sprints/{sprint_id}/health", response_model=SprintHealth)
def get_sprint_health(
    project_id: int,
    sprint_id: str,
    now: datetime | None = None,
    session: Session = Depends(get_session),  # noqa: B008 -- standard FastAPI DI idiom
) -> SprintHealth:
    _get_project(session, project_id)
    try:
        return score_sprint_health(session, project_id, sprint_id, now or DEMO_NOW)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/risks", response_model=list[RiskFinding])
def list_risks(
    project_id: int,
    session: Session = Depends(get_session),  # noqa: B008
) -> list[RiskFinding]:
    _get_project(session, project_id)
    stmt = (
        select(Risk)
        .where(Risk.project_id == project_id)
        .order_by(Risk.target_external_id)
    )
    return [_to_finding(risk) for risk in session.scalars(stmt).all()]


@router.post("/projects/{project_id}/risks/detect", response_model=list[RiskFinding])
def detect_risks(
    project_id: int,
    now: datetime | None = None,
    session: Session = Depends(get_session),  # noqa: B008
) -> list[RiskFinding]:
    _get_project(session, project_id)
    detector = StalledCriticalStoryDetector()
    findings = detector.detect(session, project_id, now or DEMO_NOW)
    persist_findings(session, project_id, findings)
    return findings


def _to_finding(risk: Risk) -> RiskFinding:
    # evidence_refs is not persisted on the Risk row (see app/models/risk.py
    # -- only reasons + trigger_signal_ids per the SCRUM-10 technical
    # design); a fresh POST .../risks/detect call returns the full
    # evidence_refs list computed in-memory.
    return RiskFinding(
        risk_type=risk.risk_type,
        target_external_id=risk.target_external_id,
        severity=risk.severity,
        confidence=risk.confidence,
        status=risk.status,
        reasons=risk.reasons,
        trigger_signal_ids=risk.trigger_signal_ids,
    )
