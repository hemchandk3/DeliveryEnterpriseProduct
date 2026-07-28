"""DEMO DATA -- CURATED, NOT LIVE.

Verbatim (structurally) transcription of the curated demo dataset locked in
docs/mvp/2026-07-24-workstream-0-narrative-and-mocks.md §4, for
`SCRUM` / DeliveryEnterprise (Jira) and `hemchandk3/DeliveryEnterpriseProduct`
(GitHub). Hand-tuned so the sprint surface reads green while `SCRUM-42` is
the single hidden, release-critical risk. Schemas mirror the real Jira Cloud
REST v3 / Agile API and GitHub REST shapes so connectors run unchanged
against this fixture and flip to live traffic once OAuth/tokens are wired up
(see workstream doc §5.3, open question 1).

This module exists so Plan 2 (Detect / risk engine) has a real, committed
fixture to score against instead of re-deriving the dataset from prose. Feed
it straight into `GitHubConnector`/`JiraConnector` via `FakeGitHubGateway`/
`FakeJiraGateway` (see `tests/fakes.py`).

DO NOT use this data to answer real questions about the project -- it is a
hand-authored scenario, not a live extract. Label any UI surface that shows
it "Demo data".
"""

PROJECT_KEY = "SCRUM"
REPO = "hemchandk3/DeliveryEnterpriseProduct"

# -- Jira sprint -------------------------------------------------------------
# Agile API `values[]` shape (GET /rest/agile/1.0/board/{id}/sprint)
SPRINT = {
    "id": 3,
    "name": "Sprint 3 — Checkout Hardening",
    "state": "active",
    "startDate": "2026-07-13T09:00:00.000+0000",
    "endDate": "2026-07-26T17:00:00.000+0000",
    "goal": "Harden checkout: payment retry, refunds, and coupon edge cases for release 1.4",
}
SPRINTS = [SPRINT]

# -- Jira issues --------------------------------------------------------------
# REST v3 `/search` `issues[]` shape.
# customfield_10016 = Story Points, customfield_10020 = Sprint (this instance
# only -- resolve via GET /rest/api/3/field before assuming these ids hold
# elsewhere).
ISSUES = [
    {
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
    },
    {
        "key": "SCRUM-45",
        "fields": {
            "summary": "Payment gateway sandbox: idempotency key support",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Dan Ohis"},
            "issuetype": {"name": "Task"},
            "priority": {"name": "High"},
            "labels": ["payments"],
            "created": "2026-07-13T09:20:00.000+0000",
            "updated": "2026-07-22T11:00:00.000+0000",
            "customfield_10016": 5,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [
                {
                    "type": {"name": "Blocks", "outward": "blocks"},
                    "outwardIssue": {
                        "key": "SCRUM-42",
                        "fields": {"status": {"name": "In Progress"}},
                    },
                }
            ],
        },
    },
    {
        "key": "SCRUM-40",
        "fields": {
            "summary": "Refund reason codes dropdown",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Dan Ohis"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "labels": ["release-1.4"],
            "created": "2026-07-13T09:00:00.000+0000",
            "updated": "2026-07-21T16:00:00.000+0000",
            "customfield_10016": 3,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-41",
        "fields": {
            "summary": "Coupon stacking validation",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Priya Nair"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "labels": [],
            "created": "2026-07-13T09:05:00.000+0000",
            "updated": "2026-07-20T10:30:00.000+0000",
            "customfield_10016": 3,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-43",
        "fields": {
            "summary": "Checkout empty-cart guard",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Mara Vlad"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "Low"},
            "labels": [],
            "created": "2026-07-14T09:00:00.000+0000",
            "updated": "2026-07-19T09:00:00.000+0000",
            "customfield_10016": 2,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-44",
        "fields": {
            "summary": "Currency rounding on tax line",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Mara Vlad"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "labels": [],
            "created": "2026-07-14T09:10:00.000+0000",
            "updated": "2026-07-21T13:00:00.000+0000",
            "customfield_10016": 3,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-46",
        "fields": {
            "summary": "Add analytics event on purchase",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Dan Ohis"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Low"},
            "labels": [],
            "created": "2026-07-15T09:00:00.000+0000",
            "updated": "2026-07-22T09:00:00.000+0000",
            "customfield_10016": 2,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-47",
        "fields": {
            "summary": "Copy update: checkout button label",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Priya Nair"},
            "issuetype": {"name": "Task"},
            "priority": {"name": "Low"},
            "labels": [],
            "created": "2026-07-15T09:00:00.000+0000",
            "updated": "2026-07-18T09:00:00.000+0000",
            "customfield_10016": 1,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-48",
        "fields": {
            "summary": "Retry backoff config toggle",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Mara Vlad"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "labels": ["release-1.4"],
            "created": "2026-07-16T09:00:00.000+0000",
            "updated": "2026-07-23T09:00:00.000+0000",
            "customfield_10016": 3,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-49",
        "fields": {
            "summary": "Checkout accessibility: focus order",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Dan Ohis"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "labels": [],
            "created": "2026-07-16T09:00:00.000+0000",
            "updated": "2026-07-23T14:00:00.000+0000",
            "customfield_10016": 3,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-50",
        "fields": {
            "summary": "Refund audit log entry",
            "status": {"name": "Done"},
            "assignee": {"displayName": "Mara Vlad"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Low"},
            "labels": [],
            "created": "2026-07-17T09:00:00.000+0000",
            "updated": "2026-07-23T10:00:00.000+0000",
            "customfield_10016": 2,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
    {
        "key": "SCRUM-51",
        "fields": {
            "summary": "Coupon expiry timezone edge case",
            "status": {"name": "To Do"},
            "assignee": {"displayName": "Priya Nair"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "Low"},
            "labels": [],
            "created": "2026-07-17T09:00:00.000+0000",
            "updated": "2026-07-17T09:00:00.000+0000",
            "customfield_10016": 2,
            "customfield_10020": [
                {"id": 3, "name": "Sprint 3 — Checkout Hardening", "state": "active"}
            ],
            "issuelinks": [],
        },
    },
]

# -- GitHub pull requests ------------------------------------------------
# REST `/pulls` shape. `reviews` and `requested_reviewers` are NOT part of
# the real `/pulls` payload -- they live behind separate endpoints
# (`/pulls/{n}/reviews`, `/pulls/{n}/requested_reviewers`), so they are kept
# as separate lookup tables below (PR_REVIEWS, PR_REQUESTED_REVIEWERS) to
# mirror how GitHubHttpGateway actually fetches them. See
# GitHubConnector.fetch in app/connectors/github.py.
PULL_REQUESTS = [
    {
        "number": 47,
        "title": "SCRUM-42: payment retry on transient gateway failure",
        "state": "open",
        "draft": False,
        "user": {"login": "priya-nair"},
        "created_at": "2026-07-17T15:00:00Z",
        "updated_at": "2026-07-18T14:20:00Z",
        "base": {"ref": "release/1.4"},
        "head": {"ref": "feature/SCRUM-42"},
    },
    {
        "number": 44,
        "title": "SCRUM-45: idempotency key support (WIP)",
        "state": "open",
        "draft": True,
        "user": {"login": "dan-ohis"},
        "created_at": "2026-07-16T11:00:00Z",
        "updated_at": "2026-07-22T11:00:00Z",
        "base": {"ref": "develop"},
        "head": {"ref": "feature/SCRUM-45"},
    },
    {
        "number": 43,
        "title": "SCRUM-41: coupon stacking validation",
        "state": "closed",
        "draft": False,
        "user": {"login": "priya-nair"},
        "created_at": "2026-07-15T10:00:00Z",
        "updated_at": "2026-07-20T10:30:00Z",
        "base": {"ref": "develop"},
        "head": {"ref": "feature/SCRUM-41"},
    },
    {
        "number": 46,
        "title": "SCRUM-48: retry backoff config toggle",
        "state": "closed",
        "draft": False,
        "user": {"login": "mara-vlad"},
        "created_at": "2026-07-18T10:00:00Z",
        "updated_at": "2026-07-23T09:00:00Z",
        "base": {"ref": "develop"},
        "head": {"ref": "feature/SCRUM-48"},
    },
]

# Keyed by PR number, as returned by GET /pulls/{n}/requested_reviewers
# (`.get("users", [])` shape).
PR_REQUESTED_REVIEWERS: dict[int, list[dict]] = {
    47: [{"login": "dan-ohis"}],
    44: [],
    43: [],
    46: [],
}

# Keyed by PR number, as returned by GET /pulls/{n}/reviews.
PR_REVIEWS: dict[int, list[dict]] = {
    47: [],  # zero approvals -- the review-starvation anomaly
    44: [],
    43: [{"user": {"login": "mara-vlad"}, "state": "APPROVED", "submitted_at": "2026-07-20T09:00:00Z"}],
    46: [{"user": {"login": "dan-ohis"}, "state": "APPROVED", "submitted_at": "2026-07-23T08:30:00Z"}],
}

# -- GitHub commits -----------------------------------------------------------
# REST `/commits` shape. Last SCRUM-42 commit is 2026-07-18 -- 6 days of
# silence relative to demo "now" (2026-07-24) while other stories keep
# committing through 2026-07-23.
COMMITS = [
    {
        "sha": "a1b2c3d",
        "commit": {
            "message": "SCRUM-42: scaffold retry policy",
            "author": {"name": "Priya Nair", "date": "2026-07-17T14:00:00Z"},
        },
        "author": {"login": "priya-nair"},
    },
    {
        "sha": "a1b2c3e",
        "commit": {
            "message": "SCRUM-42: add exponential backoff",
            "author": {"name": "Priya Nair", "date": "2026-07-18T13:50:00Z"},
        },
        "author": {"login": "priya-nair"},
    },
    {
        "sha": "b2c3d4f",
        "commit": {
            "message": "SCRUM-48: config toggle for backoff",
            "author": {"name": "Mara Vlad", "date": "2026-07-22T16:00:00Z"},
        },
        "author": {"login": "mara-vlad"},
    },
    {
        "sha": "c3d4e5a",
        "commit": {
            "message": "SCRUM-45: WIP idempotency key",
            "author": {"name": "Dan Ohis", "date": "2026-07-22T10:30:00Z"},
        },
        "author": {"login": "dan-ohis"},
    },
    {
        "sha": "d4e5f6b",
        "commit": {
            "message": "SCRUM-50: refund audit log entry",
            "author": {"name": "Mara Vlad", "date": "2026-07-23T09:30:00Z"},
        },
        "author": {"login": "mara-vlad"},
    },
]

# -- Test results & incidents (mock-only fixtures; no live source system) ----
# Not consumed by the Foundation & Ingest connectors -- kept here so Plan 2
# (Detect/Explain) can cite them without re-authoring the dataset.
TEST_RESULTS = [
    {
        "test_id": "T-1007",
        "suite": "payments",
        "name": "test_retry_on_transient_gateway_failure",
        "status": "fail",
        "branch": "feature/SCRUM-42",
        "related_issue": "SCRUM-42",
        "run_at": "2026-07-18T14:10:00Z",
    },
    {
        "test_id": "T-1002",
        "suite": "payments",
        "name": "test_coupon_stacking_rules",
        "status": "pass",
        "branch": "develop",
        "related_issue": "SCRUM-41",
        "run_at": "2026-07-20T09:10:00Z",
    },
    {
        "test_id": "T-1005",
        "suite": "checkout",
        "name": "test_backoff_toggle_reads_config",
        "status": "pass",
        "branch": "develop",
        "related_issue": "SCRUM-48",
        "run_at": "2026-07-23T08:20:00Z",
    },
]

INCIDENTS = [
    {
        "incident_id": "INC-204",
        "severity": "Sev-2",
        "title": "Elevated payment failures after 1.3 deploy",
        "component": "payments",
        "status": "open",
        "opened_at": "2026-07-16T22:00:00Z",
        "related_issue": "SCRUM-42",
        "related_pr": 47,
    },
]
