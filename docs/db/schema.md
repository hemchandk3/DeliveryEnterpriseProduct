# Data layer schema (MVP proposal)

**Status: PROPOSAL.** Authored by `dba` in parallel with the architect's
`docs/ARCHITECTURE.md` (not yet merged at the time this was written). Every
design decision below that isn't dictated by an existing, merged artifact
(PR #1's `Project`/`Signal` models, or SCRUM-12/13/14/19's acceptance
criteria) is an assumption made to produce a concrete, testable schema
rather than block on architecture sign-off. See **"Reconciliation with
ARCHITECTURE.md"** at the bottom for the full list to confirm or overrule.

This document covers the schema shipped on `feat/db-schema`: an Alembic
baseline for PR #1's `projects`/`signals` tables, plus eight new tables
for RBAC (SCRUM-14), governed agent actions (SCRUM-12/13), append-only
audit (SCRUM-13), and org-owned connections (SCRUM-19).

## Contents

- [Tables](#tables)
- [Keys & indexes](#keys--indexes)
- [Append-only audit log](#append-only-audit-log)
- [Tenant isolation / RLS plan](#tenant-isolation--rls-plan)
- [Credentials handling](#credentials-handling)
- [Migrations](#migrations)
- [Known gaps / not done here](#known-gaps--not-done-here)
- [Reconciliation with ARCHITECTURE.md](#reconciliation-with-architecturemd)

## Tables

| Table | Purpose | Introduced |
|---|---|---|
| `organizations` | Tenant root. | 0002 (new) |
| `projects` | A connected delivery project (Jira project / GitHub repo pairing). | PR #1 baseline; `organization_id` added in 0003 |
| `signals` | Normalized ingest events (issues, sprints, PRs, commits). | PR #1 baseline; `organization_id` added in 0003 |
| `roles` | RBAC role catalog: `admin`, `approver`, `viewer`. | 0004 (new) |
| `users` | Authenticated principals, scoped to one organization. | 0004 (new) |
| `user_roles` | User↔role assignment (many-to-many). | 0004 (new) |
| `connections` | An org's own GitHub/Jira connection; credential *reference* only. | 0005 (new) |
| `actions` | An agent-proposed operation, gated by approval. | 0006 (new) |
| `approvals` | The recorded human decision on an `Action`. | 0006 (new) |
| `audit_log` | Immutable, append-only governance event log. | 0007 (new) |

ORM models: `backend/app/models/{organization,project,signal,user,connection,action,approval,audit_log}.py`.
Migrations: `backend/migrations/versions/000{1..8}_*.py`.

### organizations

Tenant root. `slug` is the human-facing, URL-safe identifier; `id` is the
FK target every other table carries as `organization_id`.

### projects (extended from PR #1)

Unchanged: `id`, `name`. **Changed:** `key` was globally unique in PR #1;
it is now unique **per organization** (`uq_project_org_key` on
`(organization_id, key)`), because two organizations legitimately both
run a Jira project called e.g. "SCRUM" — see ASSUMPTION-1 below.

### signals (extended from PR #1)

Unchanged from PR #1 in every column except the addition of
`organization_id`, denormalized from `projects.organization_id` rather
than requiring a join for every tenant-scoped query or RLS policy
evaluation. The identity key SCRUM-13/the ingest AC depends on —
`(project_id, source, kind, external_id)` unique — is untouched.
`app/ingest/service.py` was updated to populate the new column from
`project.organization_id` when it upserts a signal (the connector/schema
layer, `SignalIn`, does not carry `organization_id` — it's derived, not
part of the source payload).

### roles / users / user_roles (SCRUM-14)

Three roles seeded by migration 0004: `admin`, `approver`, `viewer`. Only
`viewer`/`approver` are exercised by SCRUM-14's AC; `admin` is included
because `connections` (SCRUM-19) implies an actor who may add/disable a
connection — see ASSUMPTION-2. Users carry only a password hash
(`hashed_password`) — hashing algorithm is `security`'s call, not made
here. `email` uniqueness is scoped per organization
(`uq_user_org_email`), normalized to lowercase at the application layer
(no functional/expression index — kept portable across SQLite/Postgres
rather than dialect-specific).

`user_roles` is a join table (not a single `role` column on `users`) so a
user can hold more than one role without a future migration, even though
the MVP acceptance criteria only exercise one role per user at a time.

### connections (SCRUM-19)

`credential_ref` is an **opaque pointer** into an external secret store —
this table never stores a secret value. See
[Credentials handling](#credentials-handling). Identity is unique per
`(organization_id, source_type, instance_url, target_ref)`. `project_id`
is nullable: a connection can be tested before the internal `Project` row
it will feed exists.

### actions / approvals (SCRUM-12/13)

`actions.status` is a fast-read cache
(`PENDING_APPROVAL|APPROVED|REJECTED|EXECUTED|FAILED`, DB-CHECK
constrained) of the latest decision. The durable, evidentiary trail is
`approvals` (one row per decision) plus `audit_log` (below).
`approvals.original_steps` is a re-snapshot of `actions.proposed_steps`
taken at decision time — both AC-required "original+edited versions
recorded" and immune to any hypothetical future edit of the `Action` row.
`approver_label` is always populated (never null/generic) per SCRUM-14's
"identity is recorded in audit, never generic/system" — carried
independently of `approver_id` (which is nullable, `SET NULL` on user
deletion) so a decision's attribution survives account deactivation.
`reason` is DB-required when `decision = 'REJECTED'`
(`ck_approval_reject_reason`).

**Application-layer contract this schema cannot enforce on its own:** the
developer implementing SCRUM-13 must write the `Action.status` update and
the corresponding `AuditLog` row (and the `Approval` row) in the *same*
DB transaction. Nothing here guarantees that pairing — it's a code-review
item, not a constraint.

### audit_log (SCRUM-13)

See [Append-only audit log](#append-only-audit-log).

## Keys & indexes

- Every tenant-scoped table has a `organization_id` FK with a plain index
  (`ix_<table>_organization_id`) — used both for direct filtering and as
  the RLS policy predicate.
- `audit_log` additionally has `(organization_id, occurred_at)` composite
  index (`ix_audit_log_org_occurred_at`) for the expected access pattern:
  "this org's audit trail, newest first, paginated" — plus single-column
  indexes on `occurred_at`, `event_type`, `actor_id`, `action_id` for
  filtered views.
- `actions` is indexed on `status` and `created_at` for the approval
  queue view ("all PENDING_APPROVAL, oldest first").
- FK `ondelete` choices follow one rule: **governance evidence is never
  silently destroyed.** `actions`→`projects`, `approvals`→`actions`,
  `audit_log`→`actions` are all `RESTRICT`. Identity/display data that
  isn't evidence (`actor_id`, `approver_id`, `connections.created_by`) is
  `SET NULL` so deleting/deactivating a user doesn't block deleting the
  user — the audit/approval rows keep their point-in-time label
  (`actor_label`, `approver_label`) regardless.
- Enum-shaped columns (`status`, `decision`, `source_type`, `actor_type`,
  …) are plain `String` + `CHECK`, not a DB-native enum type. Rationale:
  Postgres `ALTER TYPE ... ADD VALUE` has locking/transaction quirks
  (can't run inside the same transaction as other DDL on some versions)
  that make adding a new status value more painful than it should be for
  an MVP that will add statuses. `CHECK` is a plain, portable ALTER.

## Append-only audit log

SCRUM-13 AC: *"Given update/delete of audit entry, Then rejected
(append-only)."* This is enforced at the DB layer, not just by ORM
convention, with two independent layers:

1. **Trigger (migration 0007, both Postgres and SQLite).** A
   `BEFORE UPDATE` / `BEFORE DELETE` trigger raises on any attempted
   mutation, regardless of which role or code path issues it. Because the
   same trigger shape exists on SQLite, `tests/test_audit_log_immutability.py`
   exercises the *real* mechanism (not a mock) even though the rest of
   the unit-test suite runs on SQLite.
2. **Privilege (migration 0008, Postgres only).** The least-privilege
   `delivery_app` role is granted `SELECT, INSERT` on `audit_log` — no
   `UPDATE`, no `DELETE`. Defense in depth: a well-behaved app can't even
   attempt the mutation; the trigger stops it even from a role that
   somehow has broader grants (e.g. an admin tool).

`AuditLog` rows snapshot identity/target as plain strings
(`actor_label`, `target_ref`) rather than relying solely on FKs to
mutable rows — a row's meaning doesn't change retroactively if a user is
renamed or a project is renamed later.

`event_type` is a free-text indexed column, not a DB enum — new event
types must not require a schema migration. The controlled vocabulary is
an application-layer concern; suggested starting set (not enforced by
the DB): `action.proposed`, `action.approved`, `action.rejected`,
`action.executed`, `action.execution_failed`, `connection.created`,
`connection.tested`, `connection.disabled`, `auth.login_failed`,
`auth.unauthorized_approval_attempt`.

## Tenant isolation / RLS plan

SCRUM-19 AC: *"Given multiple organizations, Then one organization's
connections and ingested data are never visible to another."*

**Design:** every tenant-scoped table carries a denormalized
`organization_id`. On Postgres (migration 0008):

- Row-level security is enabled on `organizations`, `projects`,
  `signals`, `users`, `connections`, `actions`, `approvals`, `audit_log`.
- Each policy predicate is
  `organization_id = current_setting('app.current_org_id', true)::integer`
  (or `id = ...` for the `organizations` table itself).
- The app must `SET LOCAL app.current_org_id = '<id>'` at the start of
  every request/transaction, after resolving the caller's organization
  from their authenticated session (SCRUM-14's session/token). This is a
  **new integration point** the `developer` needs to wire into the
  request-handling middleware/dependency layer — it does not exist yet.
- **Fail-closed by construction:** `current_setting(..., true)` returns
  `NULL` if the app forgot to set the variable, and
  `organization_id = NULL` is never true in SQL — so a request that
  forgets to scope itself sees **zero rows**, not every tenant's rows.
- The runtime app role (`delivery_app`) is a distinct, `NOLOGIN`-by-default
  Postgres role, never the schema owner — table owners bypass RLS by
  default in Postgres, so the app must run as a non-owner role for RLS to
  apply at all. Login credentials are provisioned by `devops`
  out-of-band; this migration never embeds a password.

**Not yet covered / needs `security` review:**

- `user_roles` has no `organization_id` column of its own (only
  `user_id`/`role_id`) and has no RLS policy in this proposal — scoping
  it correctly needs a subquery-based policy against `users`. The blast
  radius if left open is low (a leaked row only reveals a bare
  user_id/role_id pairing) but it should be closed before this ships.
- **This has not been executed against a live Postgres instance** — no
  Postgres was available in the sandbox this was authored in (verified:
  no `docker`, no `psql` on the box). Everything else in this PR (all 8
  migrations' `upgrade`+`downgrade`, the full model/constraint test
  suite) was run and passed against SQLite, and the Alembic-produced
  schema was diffed column-for-column against `Base.metadata` to catch
  drift — but migration 0008 (roles, grants, `CREATE POLICY`) is
  Postgres-only DDL that literally cannot run on SQLite, so it is
  reviewed-for-correctness, not executed-and-proven. `devops` should run
  it against a real/CI Postgres before merge, and `security` should
  independently review the policy predicates — this is a DBA proposal,
  not a signed-off control.
- pgvector / embedding tables are out of scope for this PR — nothing in
  SCRUM-12/13/14/19 needs them yet. Index type (ivfflat vs hnsw) and
  distance operator should be a joint `dba`+`analytics` decision made
  when the Detect/Explain scoring tables are designed.
- Time-based partitioning of `audit_log`/`signals` is deferred. Both
  tables are ID/`occurred_at`(or `ingested_at`)-indexed in a way that's
  compatible with converting to Postgres declarative range partitioning
  later, but partitioning a table complicates `downgrade` significantly
  and there is no real data volume yet to justify it. Revisit when
  `devops` has real retention/volume numbers.

## Credentials handling

`connections.credential_ref` is an opaque string pointer (e.g.
`vault://...` or a secrets-manager ARN) — **the table never stores a
credential value.** The technology behind that pointer (HashiCorp Vault,
AWS/GCP Secrets Manager, etc.) is not decided here — see ASSUMPTION-3.
`last_test_message` is documented as "non-sensitive only" but that's an
application-layer promise (the connector's error-shaping must not leak
raw response bodies or credential material into it) — `security` should
review the connector code that populates it, not just this schema.

## Migrations

```
backend/alembic.ini
backend/migrations/env.py            # reads DATABASE_URL from app.config.get_settings()
backend/migrations/script.py.mako
backend/migrations/versions/
  0001_baseline_projects_signals.py  # snapshot of PR #1 as shipped -- no schema change
  0002_organizations.py              # + bootstrap "default" org (id=1)
  0003_tenant_scope_projects_signals.py  # organization_id on projects/signals; re-scopes project key uniqueness
  0004_users_roles.py                # roles (seeded), users, user_roles
  0005_connections.py
  0006_actions_approvals.py
  0007_audit_log.py                  # + append-only trigger (Postgres + SQLite)
  0008_rls_policies.py               # Postgres-only: delivery_app role, grants, RLS policies
```

Run migrations from `backend/`:

```
pip install -e ".[dev,postgres]"   # postgres extra only needed against a real Postgres DB
alembic upgrade head
alembic downgrade base   # full rollback, tested in CI-equivalent form below
```

**Verification performed for this PR** (see PR description for full
output): `alembic upgrade head` then `alembic downgrade base` against a
scratch SQLite database (full round trip, and again stepping through
every revision one at a time, up and down); the resulting Alembic-built
schema was diffed against `Base.metadata.create_all()`'s schema (tables,
columns, unique constraints) and found identical; the full backend
pytest suite (40 tests: PR #1's 26 plus 14 new) passes; `ruff check .`
passes; `coverage` on `app/*` is 97%.

**Not performed:** anything against real Postgres (see RLS section
above) — no Postgres was available in this environment.

## Known gaps / not done here

- No FastAPI/pydantic schemas or endpoints for the new tables — this PR
  is data-layer only, per the DBA's remit. `developer` builds on these
  models.
- No RLS-session-variable wiring in the app (`SET LOCAL
  app.current_org_id`) — that's an application middleware change, not a
  schema change, and belongs with whoever implements SCRUM-14's
  authentication (`developer` + `security`).
- SQLite's foreign-key enforcement is off by default
  (`PRAGMA foreign_keys` is not set by `tests/conftest.py`'s `session`
  fixture, matching PR #1's existing test setup) — so FK `RESTRICT`/
  `SET NULL`/`CASCADE` behavior is *not* exercised by the unit-test
  suite, only by inspection of the generated DDL. `CHECK` constraints
  *are* enforced by SQLite regardless, and the new tests lean on that.
  `qa` should add FK-behavior tests against a real Postgres instance.
- No Alembic `-x db_url` documentation in a runbook yet — the env.py
  supports it (used by `tests/test_audit_log_immutability.py`) but
  `devops` should decide how CI actually invokes migrations before this
  becomes tribal knowledge.

## Reconciliation with ARCHITECTURE.md

This PR was written in parallel with the architect's
`docs/ARCHITECTURE.md`, which did not exist yet at authoring time (also:
`docs/mvp/2026-07-24-workstream-0-narrative-and-mocks.md`, referenced
heavily by PR #1's description, was not present in the repo on either
`main` or `feat/foundation-ingest` when this branch was cut — flagging in
case that's an oversight rather than intentional). The following
assumptions need explicit confirmation or correction:

1. **Multi-tenancy grain is "organization."** Nothing merged yet defines
   this. This PR introduces an `organizations` table and makes it the
   tenant boundary for RLS, adds `organization_id` to `projects` and
   `signals` (backfilled to a bootstrap "default" org in migration
   0003), and **changes `projects.key` from globally unique to unique
   per-organization** — a real behavior change from PR #1. If the
   architecture instead intends single-tenant-per-deployment (no shared
   DB across orgs) or a different tenant grain (e.g. per-connection
   rather than per-organization), this needs to be unwound before merge
   — migration 0003's downgrade is explicitly documented as data-losing
   for exactly this reason.
2. **RBAC role set.** Seeded roles are `admin`, `approver`, `viewer`.
   SCRUM-14's AC only names `viewer`/`approver`; `admin` was added by
   inference from SCRUM-19 (someone has to be authorized to add a
   connection) — the architect/security's RBAC model may define this
   differently (e.g. a separate `org_admin` vs `platform_admin`, or role
   permissions being data-driven rather than three fixed names).
3. **Secret-store technology for `connections.credential_ref` is
   undecided.** The column is a technology-agnostic opaque string by
   design, but `security`+`architect` need to pick the actual store
   (Vault, AWS/GCP Secrets Manager, etc.) so the write-only API contract
   (SCRUM-19: "never returned in a read") can be implemented against it.
4. **`Action`/`Approval` step model may not match the agent runtime's
   actual shape.** `proposed_steps`/`original_steps`/`edited_steps` are
   modeled as opaque JSON lists of `{op, ...}` — this is a guess at what
   "steps" means for SCRUM-13's "edit then approve, only approved steps
   run" AC. If the architect's agent-runtime design has a more specific
   step schema (e.g. a typed union of operation kinds), this JSON blob
   should likely become a normalized child table instead.
5. **`audit_log.evidence_signal_ids` / `actions.evidence_signal_ids`
   are plain JSON arrays of `Signal.id`,** not a join table. Chosen for
   write simplicity (one INSERT, no fan-out) since audit rows are never
   queried "by evidence signal" in the MVP's known access patterns. If
   `analytics`/`compliance` need to query "which audit entries cite
   signal X" at volume, this should become `audit_log_evidence(audit_log_id,
   signal_id)`.
6. **`user_roles` has no RLS policy** (see Tenant isolation section) —
   needs `security` sign-off either way (accept the gap for MVP, or
   require the subquery-based policy before merge).
7. **pgvector/embeddings are entirely out of scope of this PR.** Flagging
   only so it isn't assumed covered — the Detect/Explain scoring tables
   (owned jointly with `analytics`) will need their own migration(s).
