from datetime import UTC, datetime

from app.schemas.signal import SignalIn


def test_signal_in_defaults_meta_to_empty_dict():
    s = SignalIn(
        source="github",
        kind="pr",
        external_id="1",
        source_created_at=datetime(2026, 7, 1, tzinfo=UTC),
        source_updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    assert s.meta == {}
    assert s.title is None
