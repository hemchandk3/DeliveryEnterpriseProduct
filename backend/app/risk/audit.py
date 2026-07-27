"""Audit seam for the Detect stage.

SCRUM-10 AC: "Given detection complete, Then audit has a detection
record." The real append-only audit primitive (`AuditService`,
`AuditEntryIn` -- ARCHITECTURE.md §5.5/§6) is owned by SCRUM-13
(`app/govern/audit.py`), which this story's technical design flags as an
open ordering risk: "that primitive must land with or before this story."

To keep `app/risk/` decoupled from `app/govern/` (and buildable regardless
of landing order), detectors depend on this small `AuditSink` Protocol
instead of importing the concrete service. The default `NullAuditSink` is
a no-op so Detect works standalone today.

TODO(SCRUM-13): once `app/govern/audit.py::AuditService` lands, add an
adapter here (e.g. `AuditServiceSink`) that calls
`AuditService.append(AuditEntryIn(kind="DETECTION", ...))` and wire it in
at the API layer (`app/api/risk.py`) in place of `NullAuditSink()`. No
change should be needed inside `detectors.py` itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class AuditSink(Protocol):
    def record_detection(
        self, *, project_id: int, risk_type: str, findings_count: int, now: datetime
    ) -> None: ...


class NullAuditSink:
    """No-op default -- see module docstring for the SCRUM-13 seam."""

    def record_detection(
        self, *, project_id: int, risk_type: str, findings_count: int, now: datetime
    ) -> None:
        return None
