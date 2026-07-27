"""Unit tests for the pure Detect predicates (app/risk/rules.py)."""

from datetime import UTC, datetime

from app.models.signal import Signal
from app.risk.rules import (
    blocked_by_key,
    extract_issue_keys,
    has_starved_release_pr,
    is_release_gating,
    is_stale,
    last_commit_for,
)

NOW = datetime(2026, 7, 24, tzinfo=UTC)


def _issue(**overrides) -> Signal:
    defaults = {
        "id": 1,
        "project_id": 1,
        "source": "jira",
        "kind": "issue",
        "external_id": "SCRUM-42",
        "title": "Checkout payment retry",
        "state": "In Progress",
        "actor": "Priya Nair",
        "source_created_at": datetime(2026, 7, 13, 9, 15, tzinfo=UTC),
        "source_updated_at": datetime(2026, 7, 18, 14, 20, tzinfo=UTC),
        "meta": {
            "priority": "Highest",
            "labels": ["release-1.4", "critical-path", "payments"],
            "story_points": 8,
            "issuelinks": [
                {"type": "is blocked by", "direction": "inward", "key": "SCRUM-45", "status": "In Progress"}
            ],
        },
    }
    defaults.update(overrides)
    return Signal(**defaults)


def _pr(**overrides) -> Signal:
    defaults = {
        "id": 100,
        "project_id": 1,
        "source": "github",
        "kind": "pr",
        "external_id": "47",
        "title": "SCRUM-42: payment retry on transient gateway failure",
        "state": "open",
        "actor": "priya-nair",
        "source_created_at": datetime(2026, 7, 17, 15, 0, tzinfo=UTC),
        "source_updated_at": datetime(2026, 7, 18, 14, 20, tzinfo=UTC),
        "meta": {
            "draft": False,
            "base_ref": "release/1.4",
            "requested_reviewers": ["dan-ohis"],
            "reviews": [],
            "head_ref": "feature/SCRUM-42",
        },
    }
    defaults.update(overrides)
    return Signal(**defaults)


def test_extract_issue_keys_finds_keys_in_text():
    assert extract_issue_keys("SCRUM-42: payment retry") == {"SCRUM-42"}
    assert extract_issue_keys("feature/SCRUM-45") == {"SCRUM-45"}
    assert extract_issue_keys(None) == set()
    assert extract_issue_keys("no keys here") == set()


def test_is_stale_true_when_older_than_threshold():
    issue = _issue()  # updated 2026-07-18, now is 2026-07-24 -> 6 days
    assert is_stale(issue, NOW, days=5) is True
    assert is_stale(issue, NOW, days=7) is False


def test_is_release_gating_requires_highest_and_critical_path_label():
    assert is_release_gating(_issue()) is True
    assert is_release_gating(_issue(meta={"priority": "Highest", "labels": []})) is False
    assert is_release_gating(_issue(meta={"priority": "High", "labels": ["critical-path"]})) is False


def test_blocked_by_key_reads_normalized_issuelinks():
    assert blocked_by_key(_issue()) == "SCRUM-45"
    assert blocked_by_key(_issue(meta={"issuelinks": []})) is None


def test_has_starved_release_pr_matches_open_unapproved_release_pr():
    issue = _issue()
    pr = _pr()
    found = has_starved_release_pr(issue, [pr], NOW, days=5)
    assert found is pr


def test_has_starved_release_pr_none_when_pr_targets_non_release_branch():
    issue = _issue(external_id="SCRUM-45", state="In Progress")
    pr = _pr(meta={"draft": False, "base_ref": "develop", "reviews": [], "head_ref": "feature/SCRUM-45"})
    assert has_starved_release_pr(issue, [pr], NOW, days=5) is None


def test_has_starved_release_pr_none_when_approved():
    issue = _issue()
    pr = _pr(meta={
        "draft": False,
        "base_ref": "release/1.4",
        "reviews": [{"user": "dan-ohis", "state": "APPROVED"}],
        "head_ref": "feature/SCRUM-42",
    })
    assert has_starved_release_pr(issue, [pr], NOW, days=5) is None


def test_has_starved_release_pr_none_when_draft():
    issue = _issue()
    pr = _pr(meta={"draft": True, "base_ref": "release/1.4", "reviews": [], "head_ref": "feature/SCRUM-42"})
    assert has_starved_release_pr(issue, [pr], NOW, days=5) is None


def test_has_starved_release_pr_none_when_not_stale_enough():
    issue = _issue()
    pr = _pr(source_updated_at=datetime(2026, 7, 23, tzinfo=UTC))  # 1 day old
    assert has_starved_release_pr(issue, [pr], NOW, days=5) is None


def test_has_starved_release_pr_none_when_no_correlation():
    issue = _issue(external_id="SCRUM-99")
    pr = _pr()  # references SCRUM-42, not SCRUM-99
    assert has_starved_release_pr(issue, [pr], NOW, days=5) is None


def test_last_commit_for_returns_most_recent_matching_commit():
    older = Signal(
        id=1, project_id=1, source="github", kind="commit", external_id="a1b2c3d",
        title="SCRUM-42: scaffold retry policy", state=None, actor="priya-nair",
        source_created_at=datetime(2026, 7, 17, 14, 0, tzinfo=UTC),
        source_updated_at=datetime(2026, 7, 17, 14, 0, tzinfo=UTC), meta={},
    )
    newer = Signal(
        id=2, project_id=1, source="github", kind="commit", external_id="a1b2c3e",
        title="SCRUM-42: add exponential backoff", state=None, actor="priya-nair",
        source_created_at=datetime(2026, 7, 18, 13, 50, tzinfo=UTC),
        source_updated_at=datetime(2026, 7, 18, 13, 50, tzinfo=UTC), meta={},
    )
    unrelated = Signal(
        id=3, project_id=1, source="github", kind="commit", external_id="b2c3d4f",
        title="SCRUM-48: config toggle", state=None, actor="mara-vlad",
        source_created_at=datetime(2026, 7, 22, 16, 0, tzinfo=UTC),
        source_updated_at=datetime(2026, 7, 22, 16, 0, tzinfo=UTC), meta={},
    )
    result = last_commit_for("SCRUM-42", [older, newer, unrelated])
    assert result is newer


def test_last_commit_for_none_when_no_match():
    assert last_commit_for("SCRUM-99", []) is None
