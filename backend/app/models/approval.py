from datetime import UTC, datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Approval(Base):
    """The recorded human decision on an Action (SCRUM-13 / SCRUM-14 S8).

    One row per decision event. ``approver_label`` is an identity snapshot
    (never "system" / generic -- SCRUM-14 AC) taken at decision time, kept
    even if the user row is later deactivated or deleted (``approver_id``
    is SET NULL on user deletion; ``approver_label`` is not). Not made
    DB-append-only like ``audit_log`` -- only the audit_log table has that
    hard guarantee; see docs/db/schema.md for the rationale.
    """

    __tablename__ = "approvals"
    __table_args__ = (
        CheckConstraint("decision in ('APPROVED','REJECTED')", name="ck_approval_decision"),
        CheckConstraint(
            "decision <> 'REJECTED' or reason is not null", name="ck_approval_reject_reason"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    # RESTRICT, not CASCADE: an Action is never deleted once it has a
    # recorded decision -- deleting it would silently destroy governance
    # evidence. There is no delete-action feature in the MVP.
    action_id: Mapped[int] = mapped_column(
        ForeignKey("actions.id", ondelete="RESTRICT"), index=True
    )
    approver_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, default=None
    )
    approver_label: Mapped[str]
    decision: Mapped[str]
    reason: Mapped[str | None] = mapped_column(default=None)
    original_steps: Mapped[list] = mapped_column(JSON, default=list)
    edited_steps: Mapped[list | None] = mapped_column(JSON, default=None)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
