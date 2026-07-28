"""actions, approvals (SCRUM-12/13: governed agent operations)

`actions.status` is a fast-read cache of the latest decision; `approvals`
is the durable per-decision record. Neither `action_id` FK (here or in
0007's audit_log) ever cascades a delete -- actions/approvals are
permanent once written in this MVP (no delete-action feature exists).

Revision ID: 0006_actions_approvals
Revises: 0005_connections
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_actions_approvals"
down_revision: str | None = "0005_connections"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "actions",
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
            sa.ForeignKey("projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("target_ref", sa.String(), nullable=False),
        sa.Column("proposed_steps", sa.JSON(), nullable=False),
        sa.Column("evidence_signal_ids", sa.JSON(), nullable=False),
        sa.Column(
            "status", sa.String(), nullable=False, server_default="PENDING_APPROVAL"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("adapter_response", sa.JSON(), nullable=True),
        sa.CheckConstraint(
            "status in ('PENDING_APPROVAL','APPROVED','REJECTED','EXECUTED','FAILED')",
            name="ck_action_status",
        ),
    )
    op.create_index("ix_actions_organization_id", "actions", ["organization_id"])
    op.create_index("ix_actions_project_id", "actions", ["project_id"])
    op.create_index("ix_actions_agent_name", "actions", ["agent_name"])
    op.create_index("ix_actions_status", "actions", ["status"])
    op.create_index("ix_actions_created_at", "actions", ["created_at"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "action_id", sa.Integer(), sa.ForeignKey("actions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "approver_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approver_label", sa.String(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("original_steps", sa.JSON(), nullable=False),
        sa.Column("edited_steps", sa.JSON(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision in ('APPROVED','REJECTED')", name="ck_approval_decision"),
        sa.CheckConstraint(
            "decision <> 'REJECTED' or reason is not null", name="ck_approval_reject_reason"
        ),
    )
    op.create_index("ix_approvals_organization_id", "approvals", ["organization_id"])
    op.create_index("ix_approvals_action_id", "approvals", ["action_id"])
    op.create_index("ix_approvals_approver_id", "approvals", ["approver_id"])
    op.create_index("ix_approvals_decided_at", "approvals", ["decided_at"])


def downgrade() -> None:
    op.drop_table("approvals")
    op.drop_table("actions")
