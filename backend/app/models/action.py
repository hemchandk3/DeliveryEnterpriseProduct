from datetime import UTC, datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Action(Base):
    """An agent-proposed operation gated by human approval (SCRUM-12/13).

    ``status`` is a fast-read cache of the latest decision for list/filter
    views; the durable, evidentiary decision trail lives in ``approvals``
    (the decision record) and ``audit_log`` (the immutable event log). The
    developer is expected to write the ``Action`` status update and the
    ``AuditLog`` row in the *same DB transaction* -- this schema does not
    (and cannot, on its own) guarantee that pairing; see docs/db/schema.md
    "Application-layer contract".
    """

    __tablename__ = "actions"
    __table_args__ = (
        CheckConstraint(
            "status in ('PENDING_APPROVAL','APPROVED','REJECTED','EXECUTED','FAILED')",
            name="ck_action_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    agent_name: Mapped[str] = mapped_column(index=True)
    operation: Mapped[str]  # e.g. "jira.transition_issue", "github.request_review"
    target_ref: Mapped[str]  # human-readable target, e.g. "SCRUM-42" or "org/repo#47"
    # The proposed steps as the agent generated them -- immutable once
    # written (approvals.original_steps snapshots this again at decision
    # time so the two can never drift, even if this row were ever edited).
    proposed_steps: Mapped[list] = mapped_column(JSON, default=list)
    # Signal.id values that justify this proposal (Detect/Explain evidence).
    evidence_signal_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(default="PENDING_APPROVAL", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Mock-adapter response recorded at execution time (MVP: adapters are
    # mocked per SCRUM-13 "Out of scope: real system execution").
    adapter_response: Mapped[dict | None] = mapped_column(JSON, default=None)
