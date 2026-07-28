from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import Connector
from app.models import Project, Signal
from app.schemas.signal import SignalIn


class IngestService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def run(self, project: Project, connector: Connector, project_ref: str) -> int:
        written = 0
        for item in connector.fetch(project_ref):
            self._upsert(project, item)
            written += 1
        self._session.commit()
        return written

    def _upsert(self, project: Project, item: SignalIn) -> None:
        stmt = select(Signal).where(
            Signal.project_id == project.id,
            Signal.source == item.source,
            Signal.kind == item.kind,
            Signal.external_id == item.external_id,
        )
        existing = self._session.scalars(stmt).one_or_none()
        if existing is None:
            self._session.add(
                Signal(
                    # DBA note (feat/db-schema): organization_id is
                    # denormalized from project.organization_id for tenant
                    # isolation (RLS) -- see docs/db/schema.md.
                    organization_id=project.organization_id,
                    project_id=project.id,
                    source=item.source,
                    kind=item.kind,
                    external_id=item.external_id,
                    title=item.title,
                    state=item.state,
                    actor=item.actor,
                    source_created_at=item.source_created_at,
                    source_updated_at=item.source_updated_at,
                    meta=item.meta,
                )
            )
            return
        existing.title = item.title
        existing.state = item.state
        existing.actor = item.actor
        existing.source_updated_at = item.source_updated_at
        existing.meta = item.meta
        existing.ingested_at = datetime.now(UTC)
