from datetime import datetime

from pydantic import BaseModel, Field


class SignalIn(BaseModel):
    source: str
    kind: str
    external_id: str
    title: str | None = None
    state: str | None = None
    actor: str | None = None
    source_created_at: datetime
    source_updated_at: datetime
    meta: dict = Field(default_factory=dict)
