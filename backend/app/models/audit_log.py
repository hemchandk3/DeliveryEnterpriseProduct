from datetime import UTC, datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class AuditLog(Base):
    """Append-only governance record (SCRUM-13 AC: "Given update/delete of
    audit entry, Then rejected").

    Immutability is DB-enforced, not just an ORM convention -- see
    migration 0007_audit_log: on Postgres, UPDATE/DELETE privileges are
    revoked from the least-privilege app role and a trigger raises on any
    attempted UPDATE/DELETE regardless of role (defense in depth); the
    same trigger shape is created on SQLite so the unit-test suite can
    exercise the negative case. The ORM must never call ``session.delete``
    or mutate an ``AuditLog`` instance after flush -- that is an
    application-layer rule this table backs with a hard DB guarantee.

    ``actor_label``/``target_ref`` are point-in-time snapshots (not FKs to
    mutable display data) so a row's meaning never changes retroactively
    if a user is renamed or a project is renamed.
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint("actor_type in ('user','agent','system')", name="ck_audit_actor_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, index=True
    )
    # Free-text, indexed, not a DB enum -- new event types (e.g.
    # "connection.tested") must not require a schema migration. The
    # controlled vocabulary lives at the application layer; see
    # docs/db/schema.md "Audit event_type vocabulary".
    event_type: Mapped[str] = mapped_column(index=True)
    actor_type: Mapped[str]
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, default=None
    )
    actor_label: Mapped[str]
    # RESTRICT: an Action can never be deleted once audit-logged, for the
    # same evidentiary reason as approvals.action_id.
    action_id: Mapped[int | None] = mapped_column(
        ForeignKey("actions.id", ondelete="RESTRICT"), index=True, default=None
    )
    target_type: Mapped[str | None] = mapped_column(default=None)
    target_ref: Mapped[str | None] = mapped_column(default=None)
    evidence_signal_ids: Mapped[list] = mapped_column(JSON, default=list)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
