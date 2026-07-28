"""organizations (tenant root) + bootstrap "default" org

ASSUMPTION-1 (flagged for the architect, see docs/db/schema.md): the
platform is multi-tenant at the "organization" grain. Nothing in PR #1 or
the workstream-0 narrative defines this explicitly yet -- this migration
and 0003 introduce it as a DBA proposal so SCRUM-19's tenant-isolation AC
("one organization's connections and ingested data are never visible to
another") has somewhere to hang. Reconcile before merge.

Revision ID: 0002_organizations
Revises: 0001_baseline
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0002_organizations"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BOOTSTRAP_ORG_ID = 1


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    organizations = sa.table(
        "organizations",
        sa.column("id", sa.Integer),
        sa.column("slug", sa.String),
        sa.column("name", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    op.bulk_insert(
        organizations,
        [
            {
                "id": _BOOTSTRAP_ORG_ID,
                "slug": "default",
                "name": "Default Organization",
                "created_at": datetime(2026, 7, 27, tzinfo=UTC),
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("organizations")
