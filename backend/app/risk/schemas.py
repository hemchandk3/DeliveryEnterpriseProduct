"""Detect-stage response contracts (SCRUM-9, SCRUM-10).

Pinned by ARCHITECTURE.md §5.2:

    score_sprint_health(session, project_id, sprint_external_id, now) -> SprintHealth
    RiskDetector.detect(session, project_id, now) -> list[RiskFinding]

Health and risk are independent -- a raised `RiskFinding` never suppresses a
green `SprintHealth` (see AC-DETECT / SCRUM-9 acceptance criteria).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BurndownPoint(BaseModel):
    date: date
    ideal_remaining: float
    actual_remaining: float


class HealthFactor(BaseModel):
    name: str
    value: float
    weight: float
    contribution: float


class SprintHealth(BaseModel):
    sprint_external_id: str
    name: str | None = None
    status: Literal["green", "amber", "red"]
    score: float
    points_total: float
    points_done: float
    points_in_progress: float
    points_todo: float
    issues_done: int
    issues_in_progress: int
    issues_todo: int
    elapsed_days: int
    total_days: int
    burndown: list[BurndownPoint]
    factors: list[HealthFactor]


class EvidenceRef(BaseModel):
    """Lightweight pointer from a finding to a stored `Signal`.

    Explain (SCRUM-11) computes its own deterministic `Citation` set
    straight from the Signal store (see ADR-002); this is only a cheap,
    Detect-owned index of *which* signals a finding is grounded in so a
    caller can show "why" before Explain runs.
    """

    signal_id: int
    kind: str
    label: str


class RiskFinding(BaseModel):
    risk_type: str
    target_external_id: str
    severity: str
    confidence: float
    status: Literal["AT_RISK"] = "AT_RISK"
    reasons: list[str]
    trigger_signal_ids: list[int]
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
