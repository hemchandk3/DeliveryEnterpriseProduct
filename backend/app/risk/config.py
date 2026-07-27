"""Detect-stage thresholds and weights (SCRUM-9, SCRUM-10).

**Placeholder defaults only.** Per ARCHITECTURE.md §5.2 / §10 (ADR-001),
Analytics owns the final factor weights, green/amber/red thresholds, and
detector thresholds (`stale_days`, `pr_stale_days`, the `release/*`
pattern, and the severity/confidence mapping) -- tune via a comment on
SCRUM-9 / SCRUM-10, not by editing calling code.

These particular values are chosen so the curated Sprint 3 demo dataset
(`tests/fixtures/scrum_demo_data.py`) scores health **green** with
`SCRUM-42` as the single flagged risk -- i.e. they satisfy AC-DETECT, not
because they are the "correct" weighting for live data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

# Reproducible "now" for the MVP demo (single sprint window: Sprint 3 runs
# 2026-07-13 -> 2026-07-26). Production call sites (the loop runner,
# SCRUM-18) inject real `datetime.now(UTC)`; this constant is only the
# default used when an API caller omits `now`, so the demo stays
# deterministic without callers having to know the magic date.
DEMO_NOW = datetime(2026, 7, 24, tzinfo=UTC)


@dataclass(frozen=True)
class HealthWeights:
    """Sprint-health factor weights. Must sum to 1.0."""

    completion_or_active: float = 0.5
    schedule_adherence: float = 0.3
    todo_backlog: float = 0.2


@dataclass(frozen=True)
class HealthThresholds:
    green_min_score: float = 75.0
    amber_min_score: float = 50.0


@dataclass(frozen=True)
class DetectorThresholds:
    stale_days: int = 5
    pr_stale_days: int = 5
    release_branch_prefix: str = "release/"
    # An issue counts as "release-gating" on its own priority+labels (see
    # risk.rules.is_release_gating); this is a secondary points-based signal
    # that also pushes severity to "high" even if labels are missing.
    release_gating_points: int = 5
    base_confidence: float = 0.6
    confidence_per_signal: float = 0.1
    max_confidence: float = 0.95


HEALTH_WEIGHTS = HealthWeights()
HEALTH_THRESHOLDS = HealthThresholds()
DETECTOR_THRESHOLDS = DetectorThresholds()
