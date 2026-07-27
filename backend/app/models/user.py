from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Role(Base):
    """RBAC role catalog (SCRUM-14). Seeded by migration 0004 with the
    three MVP roles: admin, approver, viewer. A plain lookup table (not an
    app-level enum) so new roles can be added with a data migration, not a
    schema change.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_user_org_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    # App layer normalizes to lowercase before insert/query; the uniqueness
    # constraint is per-organization, not global (ASSUMPTION-1).
    email: Mapped[str] = mapped_column(index=True)
    display_name: Mapped[str]
    # Password hash only (bcrypt/argon2 -- algorithm choice owned by
    # `security`). Never plaintext; classify with `compliance` before any
    # PII column is added alongside this (e.g. full name, phone).
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    roles: Mapped[list["UserRole"]] = relationship(back_populates="user")


class UserRole(Base):
    """Many-to-many user<->role. MVP acceptance criteria only exercise a
    single role per user (viewer vs approver), but the join table avoids a
    future migration if a user needs >1 role (e.g. admin+approver).
    """

    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="roles")
