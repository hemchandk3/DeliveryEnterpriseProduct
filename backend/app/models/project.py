from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        # CHANGED from PR #1: `key` was globally unique. Two organizations
        # both connecting a Jira project called "SCRUM" is expected, so
        # uniqueness is now scoped per tenant. See docs/db/schema.md
        # "Reconciliation with ARCHITECTURE.md" (ASSUMPTION-1).
        UniqueConstraint("organization_id", "key", name="uq_project_org_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    key: Mapped[str] = mapped_column(index=True)
    name: Mapped[str]
