from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Connection(Base):
    """An organization's own data-source connection (SCRUM-19).

    Stores a *reference* to credentials held in an external secret store
    (Vault / cloud secrets manager -- technology TBD by `security` +
    `architect`, see docs/db/schema.md ASSUMPTION-3) -- never the secret
    itself. ``credential_ref`` is an opaque pointer (e.g. a secret-store
    path or ARN); the API that writes it is write-only and never echoes it
    back on read (that's an application-layer contract this table makes
    possible by not storing the secret at all).
    """

    __tablename__ = "connections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_type",
            "instance_url",
            "target_ref",
            name="uq_connection_identity",
        ),
        CheckConstraint("source_type in ('github', 'jira')", name="ck_connection_source_type"),
        CheckConstraint("status in ('active', 'disabled')", name="ck_connection_status"),
        CheckConstraint(
            "last_test_status is null or last_test_status in ('success', 'failure')",
            name="ck_connection_last_test_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    # Nullable: a connection can be created before the internal Project row
    # exists / is linked (e.g. admin tests a connection before an ingest
    # target project is provisioned).
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True, default=None
    )
    source_type: Mapped[str]
    instance_url: Mapped[str]
    target_ref: Mapped[str]  # e.g. "owner/repo" (GitHub) or project key (Jira)
    credential_ref: Mapped[str]  # pointer into the secret store; NEVER the secret
    status: Mapped[str] = mapped_column(default="active")
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    last_test_status: Mapped[str | None] = mapped_column(default=None)
    # Non-sensitive only -- e.g. "401 from source" not the credential or
    # raw response body. Enforced at the application layer; `security`
    # should review the connector's error-shaping before this is trusted.
    last_test_message: Mapped[str | None] = mapped_column(default=None)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
