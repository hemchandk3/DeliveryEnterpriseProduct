"""Sprint-health scoring against the curated demo dataset (SCRUM-9).

Drives AC-DETECT's health half end-to-end: ingest the real fixture through
the real connectors + IngestService, then score it exactly as the API
would (see docs/mvp/2026-07-24-workstream-0-narrative-and-mocks.md
AC-DETECT: "surface health reads green ... AND exactly one story-level
risk is raised").
"""

from datetime import UTC, datetime

import pytest

from app.risk.sprint_health import score_sprint_health
from tests.fixtures import load_demo_dataset

DEMO_NOW = datetime(2026, 7, 24, tzinfo=UTC)


@pytest.fixture()
def demo_project(session):
    return load_demo_dataset(session)


def test_sprint_3_health_reads_green(session, demo_project):
    health = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    assert health.status == "green"
    assert health.score >= 75.0


def test_sprint_3_reports_status_breakdown(session, demo_project):
    health = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    assert health.issues_done == 9
    assert health.issues_in_progress == 2
    assert health.issues_todo == 1


def test_sprint_3_reports_elapsed_and_total_days(session, demo_project):
    health = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    # Sprint runs 2026-07-13 -> 2026-07-26 (demo "now" = day 11 of 14).
    assert health.elapsed_days == 11
    assert health.total_days == 14


def test_sprint_3_reports_points_completed_vs_total(session, demo_project):
    health = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    assert health.points_total == pytest.approx(37.0)
    assert health.points_done == pytest.approx(22.0)
    assert health.points_in_progress == pytest.approx(13.0)
    assert health.points_todo == pytest.approx(2.0)
    assert health.points_done + health.points_in_progress + health.points_todo == pytest.approx(
        health.points_total
    )


def test_response_includes_burndown_series(session, demo_project):
    health = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    assert len(health.burndown) == health.elapsed_days + 1
    first, last = health.burndown[0], health.burndown[-1]
    assert first.date.isoformat() == "2026-07-13"
    assert last.date.isoformat() == "2026-07-24"
    # Ideal burndown strictly decreases toward zero remaining.
    assert last.ideal_remaining < first.ideal_remaining


def test_response_includes_named_factors(session, demo_project):
    health = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    names = {f.name for f in health.factors}
    assert names == {"completion_or_active", "schedule_adherence", "todo_backlog"}
    for factor in health.factors:
        assert 0.0 <= factor.value <= 1.0


def test_scoring_is_deterministic_across_repeated_calls(session, demo_project):
    first = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)
    second = score_sprint_health(session, demo_project.id, "3", DEMO_NOW)

    assert first.model_dump() == second.model_dump()


def test_unknown_sprint_raises_value_error(session, demo_project):
    with pytest.raises(ValueError):
        score_sprint_health(session, demo_project.id, "999", DEMO_NOW)
