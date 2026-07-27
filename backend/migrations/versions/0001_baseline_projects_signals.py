"""baseline: projects, signals (as shipped in PR #1 / feat/foundation-ingest)

This migration does not change PR #1's schema at all -- it is a literal
snapshot so `alembic upgrade head` from an empty database reproduces
exactly what `Base.metadata.create_all()` already produces today. All
subsequent migrations build on top of this baseline; do not edit it once
merged (see docs/db/schema.md).

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_projects_key", "projects", ["key"], unique=True)

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False
        ),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("state", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("source_created_at", sa.DateTime(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "source", "kind", "external_id", name="uq_signal_identity"
        ),
    )
    op.create_index("ix_signals_project_id", "signals", ["project_id"])
    op.create_index("ix_signals_source", "signals", ["source"])
    op.create_index("ix_signals_kind", "signals", ["kind"])


def downgrade() -> None:
    op.drop_table("signals")
    op.drop_table("projects")
