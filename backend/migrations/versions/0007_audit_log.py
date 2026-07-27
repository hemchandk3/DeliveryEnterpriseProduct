"""audit_log (SCRUM-13: immutable, append-only governance record)

DB-enforced immutability, not just an ORM convention:

  - A BEFORE UPDATE / BEFORE DELETE trigger raises on any attempted
    mutation of an existing row, on both Postgres and SQLite. This is the
    primary enforcement and is dialect-portable, so the negative test in
    tests/test_audit_log_immutability.py exercises the *real* guarantee
    (not a mock) even though CI/unit tests run on SQLite.
  - On Postgres, migration 0008 additionally REVOKEs UPDATE/DELETE from
    the least-privilege app role -- defense in depth (grants stop a
    well-behaved app from even attempting the mutation; the trigger stops
    it regardless of which role issues it, including a future admin
    tool that forgets this rule).

Revision ID: 0007_audit_log
Revises: 0006_actions_approvals
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_audit_log"
down_revision: str | None = "0006_actions_approvals"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=False),
        sa.Column(
            "actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_label", sa.String(), nullable=False),
        sa.Column(
            "action_id", sa.Integer(), sa.ForeignKey("actions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_ref", sa.String(), nullable=True),
        sa.Column("evidence_signal_ids", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.CheckConstraint("actor_type in ('user','agent','system')", name="ck_audit_actor_type"),
    )
    op.create_index("ix_audit_log_organization_id", "audit_log", ["organization_id"])
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])
    op.create_index("ix_audit_log_event_type", "audit_log", ["event_type"])
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_action_id", "audit_log", ["action_id"])
    op.create_index(
        "ix_audit_log_org_occurred_at", "audit_log", ["organization_id", "occurred_at"]
    )

    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION audit_log_prevent_mutation() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION
                    'audit_log is append-only: % not permitted (id=%)', TG_OP, OLD.id
                    USING ERRCODE = 'insufficient_privilege';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_audit_log_no_update
            BEFORE UPDATE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION audit_log_prevent_mutation();
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_audit_log_no_delete
            BEFORE DELETE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION audit_log_prevent_mutation();
            """
        )
    elif dialect == "sqlite":
        op.execute(
            """
            CREATE TRIGGER trg_audit_log_no_update
            BEFORE UPDATE ON audit_log
            BEGIN
                SELECT RAISE(ABORT, 'audit_log is append-only: UPDATE not permitted');
            END;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_audit_log_no_delete
            BEFORE DELETE ON audit_log
            BEGIN
                SELECT RAISE(ABORT, 'audit_log is append-only: DELETE not permitted');
            END;
            """
        )
    # Other dialects: no trigger is created. Flag to `devops`/`architect`
    # before deploying to any DB engine other than Postgres (prod) or
    # SQLite (tests) -- the append-only guarantee would be app-layer only.


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_delete ON audit_log")
        op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_update ON audit_log")
        op.execute("DROP FUNCTION IF EXISTS audit_log_prevent_mutation()")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_delete")
        op.execute("DROP TRIGGER IF EXISTS trg_audit_log_no_update")
    op.drop_table("audit_log")
