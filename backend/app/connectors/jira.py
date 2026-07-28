from datetime import datetime
from typing import Protocol

import httpx

from app.schemas.signal import SignalIn

DEFAULT_STORY_POINTS_FIELD = "customfield_10016"


class JiraGateway(Protocol):
    def search_issues(self, project_key: str) -> list[dict]: ...
    def list_sprints(self, project_key: str) -> list[dict]: ...


def _dt(value: str) -> datetime:
    # Jira uses e.g. "2026-07-01T10:00:00.000+0000"; Python 3.11+
    # fromisoformat accepts both that and a trailing "Z" natively.
    return datetime.fromisoformat(value)


def _simplify_issuelinks(issuelinks: list[dict]) -> list[dict]:
    """Normalize Jira's inward/outward issuelink shape into a flat list.

    Real payloads carry either an ``inwardIssue`` or ``outwardIssue`` per
    link, with the human-readable relationship name on ``type.inward`` /
    ``type.outward``. We flatten that into
    ``{type, direction, key, status}`` so Explain can cite it directly
    (e.g. SCRUM-42 "is blocked by" SCRUM-45).
    """
    simplified: list[dict] = []
    for link in issuelinks:
        link_type = link.get("type", {})
        if "inwardIssue" in link:
            direction = "inward"
            issue = link["inwardIssue"]
            label = link_type.get("inward") or link_type.get("name")
        elif "outwardIssue" in link:
            direction = "outward"
            issue = link["outwardIssue"]
            label = link_type.get("outward") or link_type.get("name")
        else:
            continue
        simplified.append(
            {
                "type": label,
                "direction": direction,
                "key": issue.get("key"),
                "status": ((issue.get("fields") or {}).get("status") or {}).get("name"),
            }
        )
    return simplified


class JiraConnector:
    source = "jira"

    def __init__(
        self,
        gateway: JiraGateway,
        story_points_field: str = DEFAULT_STORY_POINTS_FIELD,
    ) -> None:
        self._gateway = gateway
        # Custom field id is instance-specific; do not hardcode at call
        # sites. Resolve via GET /rest/api/3/field at OAuth time.
        self._story_points_field = story_points_field

    def fetch(self, project_ref: str) -> list[SignalIn]:
        signals: list[SignalIn] = []
        for issue in self._gateway.search_issues(project_ref):
            fields = issue["fields"]
            assignee = fields.get("assignee") or {}
            signals.append(
                SignalIn(
                    source=self.source,
                    kind="issue",
                    external_id=issue["key"],
                    title=fields.get("summary"),
                    state=(fields.get("status") or {}).get("name"),
                    actor=assignee.get("displayName"),
                    source_created_at=_dt(fields["created"]),
                    source_updated_at=_dt(fields["updated"]),
                    meta={
                        "issuetype": (fields.get("issuetype") or {}).get("name"),
                        "priority": (fields.get("priority") or {}).get("name"),
                        "labels": fields.get("labels", []),
                        "story_points": fields.get(self._story_points_field),
                        "issuelinks": _simplify_issuelinks(fields.get("issuelinks", [])),
                    },
                )
            )
        for sprint in self._gateway.list_sprints(project_ref):
            signals.append(
                SignalIn(
                    source=self.source,
                    kind="sprint",
                    external_id=str(sprint["id"]),
                    title=sprint.get("name"),
                    state=sprint.get("state"),
                    actor=None,
                    source_created_at=_dt(sprint["startDate"]),
                    source_updated_at=_dt(sprint["endDate"]),
                    meta={"goal": sprint.get("goal")},
                )
            )
        return signals


class JiraHttpGateway:
    def __init__(self, base_url: str, email: str, token: str) -> None:
        self._client = httpx.Client(base_url=base_url, auth=(email, token), timeout=30.0)

    def search_issues(self, project_key: str) -> list[dict]:
        resp = self._client.get(
            "/rest/api/3/search",
            params={"jql": f"project={project_key} ORDER BY updated DESC", "maxResults": 50},
        )
        resp.raise_for_status()
        return resp.json().get("issues", [])

    def list_sprints(self, project_key: str) -> list[dict]:
        # Board discovery + sprint listing via the Agile API.
        boards = self._client.get(
            "/rest/agile/1.0/board", params={"projectKeyOrId": project_key}
        )
        boards.raise_for_status()
        values = boards.json().get("values", [])
        if not values:
            return []
        board_id = values[0]["id"]
        sprints = self._client.get(f"/rest/agile/1.0/board/{board_id}/sprint")
        sprints.raise_for_status()
        return sprints.json().get("values", [])
