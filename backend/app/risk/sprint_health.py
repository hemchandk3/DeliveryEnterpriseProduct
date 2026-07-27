"""Sprint-health scoring (SCRUM-9).

`score_sprint_health` is a pure read over the `Signal` store: no writes,
deterministic for a fixed `now` (ARCHITECTURE.md §5.2). It reads
`kind="sprint"` and `kind="issue"` signals for the project, scopes issues
to the requested sprint, and scores burn-down/backlog health. A raised
`RiskFinding` (SCRUM-10) is computed independently in `detectors.py` and
never suppresses a green result here -- see AC-DETECT.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.risk.config import HEALTH_THRESHOLDS, HEALTH_WEIGHTS, HealthThresholds, HealthWeights
from app.risk.schemas import BurndownPoint, HealthFactor, SprintHealth

STATUS_DONE = "Done"
STATUS_IN_PROGRESS = "In Progress"
STATUS_TODO = "To Do"


def score_sprint_health(
    session: Session,
    project_id: int,
    sprint_external_id: str,
    now: datetime,
    *,
    weights: HealthWeights = HEALTH_WEIGHTS,
    thresholds: HealthThresholds = HEALTH_THRESHOLDS,
) -> SprintHealth:
    sprint = _sprint_signal(session, project_id, sprint_external_id)
    issues = _issues_for_sprint(session, project_id, sprint_external_id)

    points_total = _sum_points(issues)
    points_done = _sum_points(issues, STATUS_DONE)
    points_in_progress = _sum_points(issues, STATUS_IN_PROGRESS)
    points_todo = _sum_points(issues, STATUS_TODO)

    issues_done = _count(issues, STATUS_DONE)
    issues_in_progress = _count(issues, STATUS_IN_PROGRESS)
    issues_todo = _count(issues, STATUS_TODO)

    sprint_start = sprint.source_created_at.date()
    sprint_end = sprint.source_updated_at.date()
    total_days = max((sprint_end - sprint_start).days + 1, 1)
    elapsed_days = max(min((now.date() - sprint_start).days, total_days), 0)

    burndown = _burndown(issues, sprint_start, elapsed_days, total_days, points_total)
    today = burndown[-1] if burndown else BurndownPoint(
        date=sprint_start, ideal_remaining=points_total, actual_remaining=points_total
    )

    factors = _factors(
        points_total=points_total,
        points_done=points_done,
        points_in_progress=points_in_progress,
        points_todo=points_todo,
        today=today,
        weights=weights,
    )
    score = round(min(max(sum(f.contribution for f in factors), 0.0), 100.0), 2)
    status = _status(score, thresholds)

    return SprintHealth(
        sprint_external_id=sprint_external_id,
        name=sprint.title,
        status=status,
        score=score,
        points_total=points_total,
        points_done=points_done,
        points_in_progress=points_in_progress,
        points_todo=points_todo,
        issues_done=issues_done,
        issues_in_progress=issues_in_progress,
        issues_todo=issues_todo,
        elapsed_days=elapsed_days,
        total_days=total_days,
        burndown=burndown,
        factors=factors,
    )


def _sprint_signal(session: Session, project_id: int, sprint_external_id: str) -> Signal:
    stmt = select(Signal).where(
        Signal.project_id == project_id,
        Signal.kind == "sprint",
        Signal.external_id == sprint_external_id,
    )
    sprint = session.scalars(stmt).one_or_none()
    if sprint is None:
        raise ValueError(f"No sprint signal for project_id={project_id}, sprint={sprint_external_id!r}")
    return sprint


def _issues_for_sprint(session: Session, project_id: int, sprint_external_id: str) -> list[Signal]:
    stmt = (
        select(Signal)
        .where(Signal.project_id == project_id, Signal.kind == "issue")
        .order_by(Signal.external_id)
    )
    all_issues = list(session.scalars(stmt).all())
    scoped = [issue for issue in all_issues if _sprint_id_of(issue) == sprint_external_id]
    if scoped:
        return scoped
    # TODO(SCRUM-7): ARCHITECTURE.md §5.1 pins `jira/issue.meta.sprint{id,
    # name,state}`, but JiraConnector (app/connectors/jira.py) does not yet
    # populate it from `customfield_10020`. Until that evidence field
    # lands, every issue signal in the project is treated as belonging to
    # the queried sprint -- correct for the current single-sprint MVP
    # scope; revisit once multi-sprint live data exists.
    return all_issues


def _sprint_id_of(issue: Signal) -> str | None:
    sprint = issue.meta.get("sprint")
    if not isinstance(sprint, dict):
        return None
    sprint_id = sprint.get("id")
    return str(sprint_id) if sprint_id is not None else None


def _points(issue: Signal) -> float:
    points = issue.meta.get("story_points")
    try:
        return float(points) if points is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _sum_points(issues: list[Signal], state: str | None = None) -> float:
    return sum(_points(issue) for issue in issues if state is None or issue.state == state)


def _count(issues: list[Signal], state: str) -> int:
    return sum(1 for issue in issues if issue.state == state)


def _burndown(
    issues: list[Signal],
    sprint_start: date,
    elapsed_days: int,
    total_days: int,
    points_total: float,
) -> list[BurndownPoint]:
    """Reconstruct a daily burndown from issue `source_updated_at`.

    No per-day snapshots exist in the MVP signal store, so a day's "actual
    remaining" approximates the true burndown by treating an issue as
    burned once its last-updated timestamp lands on or before that day and
    its state is Done -- acceptable for a single sprint (ARCHITECTURE.md
    §5.2 "Risks").
    """
    points: list[BurndownPoint] = []
    for offset in range(elapsed_days + 1):
        day = sprint_start + timedelta(days=offset)
        ideal_remaining = points_total * (1 - offset / total_days) if total_days else 0.0
        done_by_day = sum(
            _points(issue)
            for issue in issues
            if issue.state == STATUS_DONE and issue.source_updated_at.date() <= day
        )
        actual_remaining = points_total - done_by_day
        points.append(
            BurndownPoint(
                date=day,
                ideal_remaining=round(ideal_remaining, 2),
                actual_remaining=round(actual_remaining, 2),
            )
        )
    return points


def _factors(
    *,
    points_total: float,
    points_done: float,
    points_in_progress: float,
    points_todo: float,
    today: BurndownPoint,
    weights: HealthWeights,
) -> list[HealthFactor]:
    def _ratio(numerator: float) -> float:
        return numerator / points_total if points_total else 1.0

    completion_or_active = _ratio(points_done + points_in_progress)
    todo_backlog = 1 - _ratio(points_todo)
    variance = abs(today.actual_remaining - today.ideal_remaining)
    schedule_adherence = 1 - (variance / points_total if points_total else 0.0)
    schedule_adherence = max(0.0, min(1.0, schedule_adherence))

    named = (
        ("completion_or_active", completion_or_active, weights.completion_or_active),
        ("schedule_adherence", schedule_adherence, weights.schedule_adherence),
        ("todo_backlog", todo_backlog, weights.todo_backlog),
    )
    return [
        HealthFactor(
            name=name,
            value=round(value, 4),
            weight=weight,
            contribution=round(value * weight * 100, 2),
        )
        for name, value, weight in named
    ]


def _status(score: float, thresholds: HealthThresholds) -> str:
    if score >= thresholds.green_min_score:
        return "green"
    if score >= thresholds.amber_min_score:
        return "amber"
    return "red"
