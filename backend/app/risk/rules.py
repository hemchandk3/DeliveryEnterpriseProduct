"""Pure detection predicates (SCRUM-10).

No I/O, no session -- everything here operates on already-loaded `Signal`
rows so it is trivially unit-testable and reusable across detectors. The
`StalledCriticalStoryDetector` (app/risk/detectors.py) is the only current
caller.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from app.models.signal import Signal

# Matches Jira-style issue keys ("SCRUM-42") inside free text -- PR titles,
# branch names, commit messages. Used to correlate a PR/commit signal back
# to the issue it implements, since `meta.head_ref` / PR title is the only
# place that link lives today (see rules module note on commit meta below).
_ISSUE_KEY_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")


def extract_issue_keys(text: str | None) -> set[str]:
    """Pull every issue key (e.g. "SCRUM-42") out of free text."""
    if not text:
        return set()
    return set(_ISSUE_KEY_PATTERN.findall(text))


def to_naive_utc(dt: datetime) -> datetime:
    """Normalize to a naive UTC datetime for safe arithmetic.

    SQLite (the test DB and the MVP default `database_url`) does not
    preserve `tzinfo` across a round trip, so a `Signal.source_updated_at`
    read back from the store is naive while an injected `now` is commonly
    tz-aware (e.g. `datetime.now(UTC)`). Both are treated as UTC so
    staleness math never raises on mixed aware/naive input.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def is_stale(signal: Signal, now: datetime, days: int) -> bool:
    """True when `signal.source_updated_at` is >= `days` old relative to `now`."""
    return (to_naive_utc(now) - to_naive_utc(signal.source_updated_at)) >= timedelta(days=days)


def is_release_gating(issue: Signal) -> bool:
    """True when an issue's own priority + labels mark it release-critical.

    Threshold/label choice is Analytics-owned (see app/risk/config.py);
    this checks the exact fields the SCRUM-10 technical design names:
    priority "Highest" and the "critical-path" label.
    """
    meta = issue.meta
    labels = meta.get("labels") or []
    return meta.get("priority") == "Highest" and "critical-path" in labels


def blocked_by_key(issue: Signal) -> str | None:
    """Return the key of an issue this one "is blocked by", if any.

    Reads the flattened `issuelinks` shape JiraConnector normalizes
    (app/connectors/jira.py::_simplify_issuelinks):
    `{type, direction, key, status}`.
    """
    for link in issue.meta.get("issuelinks") or []:
        if (link.get("type") or "").strip().lower() == "is blocked by":
            return link.get("key")
    return None


def has_starved_release_pr(
    issue: Signal,
    prs: list[Signal],
    now: datetime,
    days: int,
    release_prefix: str = "release/",
) -> Signal | None:
    """Return the correlated PR that starves `issue`'s release, or None.

    A PR "starves" the issue's release when it: targets a `release/*`
    branch, is open and non-draft, references the issue (by title or
    `meta.head_ref` -- PR↔issue correlation is heuristic, per the SCRUM-10
    technical design), carries zero `APPROVED` reviews, and has been in
    that state for >= `days`.
    """
    for pr in sorted(prs, key=lambda p: p.external_id):
        meta = pr.meta
        base_ref = meta.get("base_ref") or ""
        if not base_ref.startswith(release_prefix):
            continue
        if pr.state != "open" or meta.get("draft", False):
            continue
        referenced = extract_issue_keys(pr.title) | extract_issue_keys(meta.get("head_ref"))
        if issue.external_id not in referenced:
            continue
        reviews = meta.get("reviews") or []
        if any(review.get("state") == "APPROVED" for review in reviews):
            continue
        if not is_stale(pr, now, days):
            continue
        return pr
    return None


def last_commit_for(issue_key: str, commits: list[Signal]) -> Signal | None:
    """Most recent commit signal that references `issue_key` (by title).

    Commit `meta.issue_keys` is pinned by ARCHITECTURE.md §5.1 but not yet
    populated by GitHubConnector -- see TODO in
    app/risk/detectors.py::_last_commit_for. Falls back to parsing the
    commit title (`meta.message` is not normalized either; the connector
    stores the first line as `Signal.title`), which is sufficient for the
    curated demo dataset and any commit message that follows the
    "SCRUM-nn: ..." convention.
    """
    matches = [c for c in commits if issue_key in extract_issue_keys(c.title)]
    if not matches:
        return None
    return max(matches, key=lambda c: c.source_created_at)
