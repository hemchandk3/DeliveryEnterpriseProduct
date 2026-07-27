from app.risk.schemas import BurndownPoint, EvidenceRef, HealthFactor, RiskFinding, SprintHealth


def test_risk_finding_defaults_evidence_refs_and_status():
    finding = RiskFinding(
        risk_type="stalled_critical_story",
        target_external_id="SCRUM-42",
        severity="high",
        confidence=0.9,
        reasons=["reason"],
        trigger_signal_ids=[1, 2],
    )
    assert finding.status == "AT_RISK"
    assert finding.evidence_refs == []


def test_sprint_health_round_trips_nested_models():
    health = SprintHealth(
        sprint_external_id="3",
        name="Sprint 3",
        status="green",
        score=90.5,
        points_total=37,
        points_done=22,
        points_in_progress=13,
        points_todo=2,
        issues_done=9,
        issues_in_progress=2,
        issues_todo=1,
        elapsed_days=11,
        total_days=14,
        burndown=[BurndownPoint(date="2026-07-13", ideal_remaining=37, actual_remaining=37)],
        factors=[HealthFactor(name="completion_or_active", value=0.94, weight=0.5, contribution=47.3)],
    )
    dumped = health.model_dump()
    assert dumped["status"] == "green"
    assert dumped["burndown"][0]["ideal_remaining"] == 37
    assert dumped["factors"][0]["name"] == "completion_or_active"


def test_evidence_ref_is_a_plain_pointer():
    ref = EvidenceRef(signal_id=1, kind="jira/issue", label="SCRUM-42")
    assert ref.signal_id == 1
