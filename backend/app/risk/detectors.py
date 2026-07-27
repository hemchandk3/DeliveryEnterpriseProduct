"""Hidden-risk detection (SCRUM-10).

`RiskDetector` is the seam other risk templates would implement (out of
MVP scope -- see docs/mvp workstream #0 §"Out of scope"); the MVP ships
exactly one: `StalledCriticalStoryDetector`, which flags a release-critical
story that has gone quiet behind PR review starvation, per the locked demo
narrative (docs/mvp/2026-07-24-workstream-0-narrative-and-mocks.md §1.2)
and AC-DETECT.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.risk.audit import AuditSink, NullAuditSink
from app.risk.config import DETECTOR_THRESHOLDS, DetectorThresholds
from app.risk.rules import (
    blocked_by_key,
    has_starved_release_pr,
    is_release_gating,
    is_stale,
    last_commit_for,
    to_naive_utc,
)
from app.risk.schemas import EvidenceRef, RiskFinding

STATUS_IN_PROGRESS = "In Progress"


class RiskDetector(Protocol):
    def detect(self, session: Session, project_id: int, now: datetime) -> list[RiskFinding]: ...


class StalledCriticalStoryDetector:
    """Flags an In-Progress, release-gating story stalled behind an
    unapproved PR on a `release/*` branch (SCRUM-10 technical design).

    AT_RISK when: `issue.state == "In Progress"` AND `source_updated_at`
    is >= `stale_days` old in the active sprint AND there is a correlated
    open, non-draft PR targeting `release/*` with zero `APPROVED` reviews
    for >= `pr_stale_days`.
    """

    risk_type = "stalled_critical_story"

    def __init__(
        self,
        thresholds: DetectorThresholds = DETECTOR_THRESHOLDS,
        audit: AuditSink | None = None,
    ) -> None:
        self._thresholds = thresholds
        # SCRUM-13 seam -- see app/risk/audit.py module docstring.
        self._audit = audit or NullAuditSink()

    def detect(self, session: Session, project_id: int, now: datetime) -> list[RiskFinding]:
        issues = _signals(session, project_id, "issue")
        prs = _signals(session, project_id, "pr")
        commits = _signals(session, project_id, "commit")

        findings: list[RiskFinding] = []
        for issue in issues:
            if issue.state != STATUS_IN_PROGRESS:
                continue
            if not is_stale(issue, now, self._thresholds.stale_days):
                continue
            starved_pr = has_starved_release_pr(
                issue,
                prs,
                now,
                self._thresholds.pr_stale_days,
                self._thresholds.release_branch_prefix,
            )
            if starved_pr is None:
                continue
            findings.append(self._build_finding(issue, starved_pr, commits, now))

        self._audit.record_detection(
            project_id=project_id,
            risk_type=self.risk_type,
            findings_count=len(findings),
            now=now,
        )
        return findings

    def _build_finding(
        self, issue: Signal, pr: Signal, commits: list[Signal], now: datetime
    ) -> RiskFinding:
        last_commit = last_commit_for(issue.external_id, commits)

        reasons = _reasons(issue, pr, last_commit, now)

        trigger_signal_ids = {issue.id, pr.id}
        if last_commit is not None:
            trigger_signal_ids.add(last_commit.id)

        evidence_refs = [
            EvidenceRef(signal_id=issue.id, kind="jira/issue", label=issue.external_id),
            EvidenceRef(signal_id=pr.id, kind="github/pr", label=f"PR #{pr.external_id}"),
        ]
        if last_commit is not None:
            evidence_refs.append(
                EvidenceRef(
                    signal_id=last_commit.id,
                    kind="github/commit",
                    label=last_commit.external_id[:7],
                )
            )

        severity, confidence = _severity_and_confidence(issue, last_commit, self._thresholds)

        return RiskFinding(
            risk_type=self.risk_type,
            target_external_id=issue.external_id,
            severity=severity,
            confidence=confidence,
            status="AT_RISK",
            reasons=reasons,
            trigger_signal_ids=sorted(trigger_signal_ids),
            evidence_refs=evidence_refs,
        )


def _signals(session: Session, project_id: int, kind: str) -> list[Signal]:
    stmt = (
        select(Signal)
        .where(Signal.project_id == project_id, Signal.kind == kind)
        .order_by(Signal.external_id)
    )
    return list(session.scalars(stmt).all())


def _reasons(issue: Signal, pr: Signal, last_commit: Signal | None, now: datetime) -> list[str]:
    meta = issue.meta
    stale_days = (to_naive_utc(now) - to_naive_utc(issue.source_updated_at)).days
    pr_stale_days = (to_naive_utc(now) - to_naive_utc(pr.source_updated_at)).days

    reasons = [
        (
            f"{issue.external_id} is In Progress but last updated "
            f"{issue.source_updated_at.date().isoformat()} ({stale_days}d stale) in the active sprint"
        ),
        (
            f"PR #{pr.external_id} targets {pr.meta.get('base_ref')}, is open and non-draft, "
            f"with zero APPROVED reviews after {pr_stale_days}d"
        ),
    ]
    if last_commit is not None:
        reasons.append(
            f"last commit touching {issue.external_id} was "
            f"{last_commit.source_created_at.date().isoformat()}"
        )
    if is_release_gating(issue):
        labels = ", ".join(meta.get("labels") or [])
        points = meta.get("story_points")
        reasons.append(
            f"release-gating: priority {meta.get('priority')}, labels [{labels}], {points}pts"
        )
    blocked_by = blocked_by_key(issue)
    if blocked_by:
        reasons.append(f"is blocked by {blocked_by}")
    return reasons


def _severity_and_confidence(
    issue: Signal, last_commit: Signal | None, thresholds: DetectorThresholds
) -> tuple[str, float]:
    points = issue.meta.get("story_points") or 0
    release_gating = is_release_gating(issue)
    severity = "high" if (release_gating or points >= thresholds.release_gating_points) else "medium"

    corroborating_signals = 2  # stale issue + starved PR are always present
    if last_commit is not None:
        corroborating_signals += 1
    if release_gating:
        corroborating_signals += 1
    if blocked_by_key(issue):
        corroborating_signals += 1

    confidence = min(
        thresholds.base_confidence + thresholds.confidence_per_signal * corroborating_signals,
        thresholds.max_confidence,
    )
    return severity, round(confidence, 2)
