"""connections (SCRUM-19: org-owned data-source connections)

`credential_ref` is an opaque pointer into an external secret store --
this table never stores a secret value. See docs/db/schema.md
"Credentials handling" and ASSUMPTION-3 (secret-store technology TBD).

Revision ID: 0005_connections
Revises: 0004_users_roles
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_connections"
down_revision: str | None = "0004_users_roles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("instance_url", sa.String(), nullable=False),
        sa.Column("target_ref", sa.String(), nullable=False),
        sa.Column("credential_ref", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("last_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_status", sa.String(), nullable=True),
        sa.Column("last_test_message", sa.String(), nullable=True),
        sa.Column(
            "created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "organization_id",
            "source_type",
            "instance_url",
            "target_ref",
            name="uq_connection_identity",
        ),
        sa.CheckConstraint(
            "source_type in ('github', 'jira')", name="ck_connection_source_type"
        ),
        sa.CheckConstraint("status in ('active', 'disabled')", name="ck_connection_status"),
        sa.CheckConstraint(
            "last_test_status is null or last_test_status in ('success', 'failure')",
            name="ck_connection_last_test_status",
        ),
    )
    op.create_index("ix_connections_organization_id", "connections", ["organization_id"])
    op.create_index("ix_connections_project_id", "connections", ["project_id"])


def downgrade() -> None:
    op.drop_table("connections")
