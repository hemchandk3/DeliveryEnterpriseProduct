from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "source", "kind", "external_id", name="uq_signal_identity"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    source: Mapped[str] = mapped_column(index=True)  # "github" | "jira"
    kind: Mapped[str] = mapped_column(index=True)  # "pr" | "commit" | "issue" | "sprint"
    external_id: Mapped[str]
    title: Mapped[str | None] = mapped_column(default=None)
    state: Mapped[str | None] = mapped_column(default=None)
    actor: Mapped[str | None] = mapped_column(default=None)
    source_created_at: Mapped[datetime]
    source_updated_at: Mapped[datetime]
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(default=_now)
