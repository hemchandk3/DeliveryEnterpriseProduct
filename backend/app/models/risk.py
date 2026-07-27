from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Risk(Base):
    """A persisted Detect-stage finding (SCRUM-10).

    Unique on `(project_id, risk_type, target_external_id)` so re-running
    detection upserts in place instead of duplicating (see
    app/risk/persistence.py).
    """

    __tablename__ = "risks"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "risk_type", "target_external_id", name="uq_risk_identity"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    risk_type: Mapped[str] = mapped_column(index=True)
    target_external_id: Mapped[str]
    severity: Mapped[str]
    confidence: Mapped[float]
    status: Mapped[str]
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    trigger_signal_ids: Mapped[list] = mapped_column(JSON, default=list)
    detected_at: Mapped[datetime] = mapped_column(default=_now)
