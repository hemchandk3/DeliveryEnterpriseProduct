"""least-privilege app role + row-level security (Postgres only)

This migration is a no-op on any dialect other than 'postgresql' (SQLite
has neither roles nor RLS) -- the round-trip smoke test therefore only
proves this migration *runs cleanly end to end*, not that the RLS
policies below are correct under load or against real Postgres. **This
has not been executed against a live Postgres instance in this session
(no Postgres was available in the sandbox this was authored in).**
`devops`/`security` must smoke-test this migration against a real
Postgres (or a CI Postgres service container) before it is trusted, and
`security` should independently review the policy predicates below --
this is a DBA proposal, not a signed-off security control.

Design:

  - `delivery_app`: the runtime role the FastAPI app connects as. Never a
    superuser, never the schema owner. Login credentials (password / IAM
    auth) are provisioned out-of-band by `devops` -- this migration only
    defines the role and its privileges, never a password.
  - RLS is enabled on every tenant-scoped table, predicated on the
    Postgres session variable `app.current_org_id`, which the app must
    `SET LOCAL app.current_org_id = '<id>'` at the start of every
    request/transaction after resolving the caller's organization from
    their authenticated session (see docs/db/schema.md "Tenant isolation
    / RLS plan"). `current_setting(..., true)` (missing_ok=true) makes an
    unset variable evaluate to NULL rather than erroring, and
    `organization_id = NULL` is never true -- so a request that forgets
    to set the session variable sees ZERO rows (fail closed), not every
    tenant's rows (fail open).
  - `audit_log` is granted SELECT + INSERT only -- no UPDATE, no DELETE,
    reinforcing the trigger from 0007 with a privilege boundary.
  - `organizations` and `roles` are read-only to the app role: tenant
    onboarding (creating a new Organization) and role-catalog changes are
    privileged/admin operations run by the migrator role, not the
    request-serving app role.
  - `user_roles` is intentionally NOT given its own RLS policy in this
    migration -- it has no organization_id column of its own (only
    user_id/role_id) and scoping it would require a subquery-based policy
    against `users`. Flagged as a known gap for `security` review; the
    blast radius if skipped is low (a leaked row only reveals a bare
    user_id/role_id pairing, not content) but it should still be closed
    before this ships. See docs/db/schema.md "Reconciliation".

Revision ID: 0008_rls_policies
Revises: 0007_audit_log
Create Date: 2026-07-27

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008_rls_policies"
down_revision: str | None = "0007_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_APP_ROLE = "delivery_app"

# (table, organization-scoping column) for the standard tenant policy.
_TENANT_TABLES = [
    ("projects", "organization_id"),
    ("signals", "organization_id"),
    ("users", "organization_id"),
    ("connections", "organization_id"),
    ("actions", "organization_id"),
    ("approvals", "organization_id"),
]


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{_APP_ROLE}') THEN
                CREATE ROLE {_APP_ROLE} NOLOGIN;
            END IF;
        END
        $$;
        """
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {_APP_ROLE}")
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {_APP_ROLE}")

    # Read-only catalogs: onboarding a tenant / changing the role catalog
    # is a privileged/admin operation, not part of the app's normal
    # per-request path.
    op.execute(f"GRANT SELECT ON organizations, roles TO {_APP_ROLE}")

    # Standard CRUD tables.
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON "
        f"projects, signals, users, user_roles, connections, actions, approvals "
        f"TO {_APP_ROLE}"
    )

    # audit_log: append-only at the privilege layer too (0007's trigger is
    # the primary guarantee; this is defense in depth).
    op.execute(f"GRANT SELECT, INSERT ON audit_log TO {_APP_ROLE}")

    # organizations: app can read its own org row (e.g. an org settings
    # page) but never write -- onboarding is a separate privileged flow.
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_organizations ON organizations
        FOR SELECT
        USING (id = current_setting('app.current_org_id', true)::integer)
        """
    )

    for table, column in _TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING ({column} = current_setting('app.current_org_id', true)::integer)
            WITH CHECK ({column} = current_setting('app.current_org_id', true)::integer)
            """
        )

    # audit_log: same read scoping as the other tables, but the INSERT
    # side is intentionally permissive on the WITH CHECK beyond the
    # organization match (governance writes must always succeed) --
    # WITH CHECK still requires organization_id to match the caller's
    # session so a request can only ever audit-log against its own org.
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_audit_log ON audit_log
        USING (organization_id = current_setting('app.current_org_id', true)::integer)
        WITH CHECK (organization_id = current_setting('app.current_org_id', true)::integer)
        """
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute("DROP POLICY IF EXISTS tenant_isolation_audit_log ON audit_log")
    op.execute("ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY")

    for table, _column in _TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS tenant_isolation_organizations ON organizations")
    op.execute("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY")

    op.execute(f"REVOKE ALL ON audit_log FROM {_APP_ROLE}")
    op.execute(
        f"REVOKE ALL ON "
        f"projects, signals, users, user_roles, connections, actions, approvals "
        f"FROM {_APP_ROLE}"
    )
    op.execute(f"REVOKE ALL ON organizations, roles FROM {_APP_ROLE}")
    op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {_APP_ROLE}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {_APP_ROLE}")
    # DROP ROLE is intentionally omitted: if devops has attached login
    # credentials to this role out-of-band, dropping it here would be a
    # surprise destructive action outside this migration's ownership.
    # Leaving an unused, privilege-less role behind is safe; provisioning
    # scripts should DROP ROLE explicitly if it's truly retired.
