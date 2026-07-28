from app.connectors.jira import JiraConnector
from tests.fakes import FakeJiraGateway

# SCRUM-42 mock row, verbatim from docs/mvp/2026-07-24-workstream-0-narrative-and-mocks.md
# §4.2 -- the one hidden, release-critical risk the whole demo hinges on.
SCRUM_42 = {
    "key": "SCRUM-42",
    "fields": {
        "summary": "Checkout payment retry on transient gateway failure",
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Priya Nair"},
        "issuetype": {"name": "Story"},
        "priority": {"name": "Highest"},
        "labels": ["release-1.4", "critical-path", "payments"],
        "created": "2026-07-13T09:15:00.000+0000",
        "updated": "2026-07-18T14:20:00.000+0000",
        "customfield_10016": 8,
        "customfield_10020": [
            {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
        ],
        "issuelinks": [
            {
                "type": {"name": "Blocks", "inward": "is blocked by"},
                "inwardIssue": {
                    "key": "SCRUM-45",
                    "fields": {"status": {"name": "In Progress"}},
                },
            }
        ],
    },
}


def test_fetch_normalizes_issues_and_sprints():
    gateway = FakeJiraGateway(
        issues=[
            {
                "key": "SCRUM-1",
                "fields": {
                    "summary": "Build ingest",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Alice"},
                    "issuetype": {"name": "Story"},
                    "created": "2026-07-01T10:00:00.000+0000",
                    "updated": "2026-07-02T10:00:00.000+0000",
                },
            }
        ],
        sprints=[
            {
                "id": 5,
                "name": "Sprint 1",
                "state": "active",
                "goal": "Ship ingest",
                "startDate": "2026-07-01T00:00:00.000+0000",
                "endDate": "2026-07-14T00:00:00.000+0000",
            }
        ],
    )

    signals = JiraConnector(gateway).fetch("SCRUM")

    issue = next(s for s in signals if s.kind == "issue")
    assert issue.external_id == "SCRUM-1"
    assert issue.state == "In Progress"
    assert issue.actor == "Alice"
    assert issue.meta["issuetype"] == "Story"
    # No priority/labels/issuelinks on this minimal issue -- meta still
    # carries the keys with empty/None defaults, never raises.
    assert issue.meta["priority"] is None
    assert issue.meta["labels"] == []
    assert issue.meta["story_points"] is None
    assert issue.meta["issuelinks"] == []
    sprint = next(s for s in signals if s.kind == "sprint")
    assert sprint.external_id == "5"
    assert sprint.state == "active"


def test_fetch_enriches_scrum_42_with_evidence_meta():
    """Fold-in: Workstream #0 §5.2 evidence extension, asserted against the
    real SCRUM-42 mock row (evidence signal #2 and #5 in the narrative)."""
    gateway = FakeJiraGateway(issues=[SCRUM_42], sprints=[])

    signals = JiraConnector(gateway).fetch("SCRUM")

    issue = signals[0]
    assert issue.external_id == "SCRUM-42"
    assert issue.meta["priority"] == "Highest"
    assert issue.meta["labels"] == ["release-1.4", "critical-path", "payments"]
    assert issue.meta["story_points"] == 8
    assert issue.meta["issuelinks"] == [
        {
            "type": "is blocked by",
            "direction": "inward",
            "key": "SCRUM-45",
            "status": "In Progress",
        }
    ]


def test_story_points_field_id_is_configurable():
    issue = {
        "key": "SCRUM-42",
        "fields": {
            **SCRUM_42["fields"],
            "customfield_10016": None,
            "customfield_99999": 13,
        },
    }
    gateway = FakeJiraGateway(issues=[issue], sprints=[])

    signals = JiraConnector(gateway, story_points_field="customfield_99999").fetch("SCRUM")

    assert signals[0].meta["story_points"] == 13
