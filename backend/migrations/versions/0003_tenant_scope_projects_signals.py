"""tenant-scope projects and signals (organization_id)

Adds `organization_id` to `projects` and `signals`, backfills every
existing row to the bootstrap "default" organization (id=1, from 0002),
then enforces NOT NULL + FK + index. Also re-scopes `projects.key`
uniqueness from global to per-tenant (organization_id, key) -- CHANGED
from PR #1, see ASSUMPTION-1 in docs/db/schema.md.

Lock / performance note: on Postgres this runs as ADD COLUMN (fast,
metadata-only) + UPDATE (full table rewrite of touched rows) + SET NOT
NULL (requires a full table scan to validate, holds ACCESS EXCLUSIVE
briefly). Both tables are empty/near-empty at this point in the project's
life; on a populated table this three-step shape (nullable -> backfill ->
NOT NULL) is still the right pattern to avoid a long-held exclusive lock,
but the SET NOT NULL scan would need to run with `NOT VALID` / manual
validation staging for a large table -- flag to `devops`/`architect`
before running this against real data.

Guardrail note: the downgrade is DATA-LOSING (it drops organization_id
and therefore all tenant attribution). Do not run against a populated
database without a verified backup and explicit sign-off.

Revision ID: 0003_tenant_scope
Revises: 0002_organizations
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_tenant_scope"
down_revision: str | None = "0002_organizations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BOOTSTRAP_ORG_ID = 1


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))
    with op.batch_alter_table("signals") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.Integer(), nullable=True))

    # Backfill: every pre-existing row belongs to the bootstrap org. On a
    # real cutover with more than one intended tenant, this backfill would
    # instead be driven by an out-of-band project->organization mapping
    # supplied by whoever is doing the tenant split -- not assumed here.
    projects = sa.table(
        "projects", sa.column("id", sa.Integer), sa.column("organization_id", sa.Integer)
    )
    signals = sa.table(
        "signals", sa.column("id", sa.Integer), sa.column("organization_id", sa.Integer)
    )
    op.execute(projects.update().values(organization_id=_BOOTSTRAP_ORG_ID))
    op.execute(signals.update().values(organization_id=_BOOTSTRAP_ORG_ID))

    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_projects_organization_id",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.drop_index("ix_projects_key")
        batch_op.create_index("ix_projects_key", ["key"])
        batch_op.create_unique_constraint("uq_project_org_key", ["organization_id", "key"])
        batch_op.create_index("ix_projects_organization_id", ["organization_id"])

    with op.batch_alter_table("signals") as batch_op:
        batch_op.alter_column("organization_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_signals_organization_id",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_index("ix_signals_organization_id", ["organization_id"])


def downgrade() -> None:
    with op.batch_alter_table("signals") as batch_op:
        batch_op.drop_index("ix_signals_organization_id")
        batch_op.drop_constraint("fk_signals_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")

    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_index("ix_projects_organization_id")
        batch_op.drop_constraint("uq_project_org_key", type_="unique")
        batch_op.drop_index("ix_projects_key")
        batch_op.drop_constraint("fk_projects_organization_id", type_="foreignkey")
        batch_op.drop_column("organization_id")
        batch_op.create_index("ix_projects_key", ["key"], unique=True)
