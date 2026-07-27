"""Proves the DB-enforced append-only guarantee on audit_log (SCRUM-13 AC:
"Given update/delete of audit entry, Then rejected").

IMPORTANT: this only exercises the SQLite trigger from migration
0007_audit_log (see conftest.py's `session` fixture -- it builds the
schema via `Base.metadata.create_all()`, not via Alembic, so it does NOT
include the trigger). This module therefore runs the real migration
against a throwaway file-backed SQLite DB instead of using the shared
`session` fixture, so the trigger is actually present when we try to
break it. The Postgres-only privilege layer (migration 0008: REVOKE
UPDATE/DELETE from the app role) is NOT exercised here -- there is no
Postgres in this test environment; `qa`/`devops` should add an
equivalent negative test against a real Postgres instance before this
ships (see docs/db/schema.md "Reconciliation").
"""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture()
def migrated_session(tmp_path):
    db_path = tmp_path / f"audit_{uuid.uuid4().hex}.db"
    db_url = f"sqlite:///{db_path}"

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.attributes["configure_logger"] = False
    # Route env.py at the scratch DB via `-x db_url=...` rather than the
    # process-wide, lru_cache'd `app.config.get_settings()` -- avoids
    # cross-test contamination from other test modules that may have
    # already cached settings by the time this fixture runs.
    cfg.cmd_opts = argparse.Namespace(x=[f"db_url={db_url}"])

    command.upgrade(cfg, "head")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _insert_audit_row(session) -> int:
    result = session.execute(
        text(
            """
            INSERT INTO audit_log
                (organization_id, occurred_at, event_type, actor_type,
                 actor_label, evidence_signal_ids, payload)
            VALUES
                (1, '2026-07-27 00:00:00', 'action.approved', 'user',
                 'pm-approver@example.com', '[]', '{}')
            """
        )
    )
    session.commit()
    return result.lastrowid


def test_audit_log_insert_succeeds(migrated_session):
    row_id = _insert_audit_row(migrated_session)
    assert row_id is not None
    row = migrated_session.execute(
        text("SELECT event_type FROM audit_log WHERE id = :id"), {"id": row_id}
    ).one()
    assert row.event_type == "action.approved"


def test_audit_log_update_is_rejected(migrated_session):
    row_id = _insert_audit_row(migrated_session)

    with pytest.raises(IntegrityError, match="append-only"):
        migrated_session.execute(
            text("UPDATE audit_log SET event_type = 'tampered' WHERE id = :id"),
            {"id": row_id},
        )
        migrated_session.commit()
    migrated_session.rollback()

    row = migrated_session.execute(
        text("SELECT event_type FROM audit_log WHERE id = :id"), {"id": row_id}
    ).one()
    assert row.event_type == "action.approved"


def test_audit_log_delete_is_rejected(migrated_session):
    row_id = _insert_audit_row(migrated_session)

    with pytest.raises(IntegrityError, match="append-only"):
        migrated_session.execute(
            text("DELETE FROM audit_log WHERE id = :id"), {"id": row_id}
        )
        migrated_session.commit()
    migrated_session.rollback()

    count = migrated_session.execute(
        text("SELECT count(*) FROM audit_log WHERE id = :id"), {"id": row_id}
    ).scalar_one()
    assert count == 1
