from typing import Protocol, runtime_checkable

from app.schemas.signal import SignalIn


@runtime_checkable
class Connector(Protocol):
    source: str

    def fetch(self, project_ref: str) -> list[SignalIn]: ...
