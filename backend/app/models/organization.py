from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Organization(Base):
    """The tenant root.

    Every tenant-scoped table in this schema (projects, signals, users,
    connections, actions, approvals, audit_log) carries a denormalized
    ``organization_id`` FK back to this table -- used both for query
    scoping and as the row-level-security predicate. See
    docs/db/schema.md ("Tenant isolation / RLS plan") for the full design
    and the assumptions it rests on (ASSUMPTION-1: this platform is
    multi-tenant at the "organization" grain).
    """

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
