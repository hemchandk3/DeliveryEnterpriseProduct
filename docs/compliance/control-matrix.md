# Compliance Control Matrix — MVP Governance Gate

**Owner:** Compliance. **Status:** Baseline for the 100% compliance gate (`docs/ENGINEERING_STANDARDS.md` §3).
**Scope:** the four governance-bearing stories of the MVP loop — **SCRUM-13** (approval + immutable audit),
**SCRUM-14** (auth/RBAC), **SCRUM-15** (executive report), **SCRUM-19** (org connections / credential store) —
plus the **PII exposure introduced by the merged foundation code** (SCRUM-7 `actor`).
**Reviewed against:** `docs/ARCHITECTURE.md` (main), `docs/security/{threat-model,rbac,secret-handling}.md`,
PR #1 (`feat/foundation-ingest`, merged ingest), PR #7 (`feat/db-schema`, **proposal, unmerged**).

---

## 0. How to read this matrix — "designed for" vs "demonstrated"

Per the Compliance guardrail (**no claim without evidence**), every control carries a **State**:

| State | Meaning |
|---|---|
| **DEMONSTRATED** | A traceable artifact proves the control works against real behavior (test output, executed migration, live run). |
| **DESIGNED** | The control exists on paper or in unmerged/data-layer code, but no behavioral evidence yet. Not gate-passing. |
| **ABSENT** | No design and no code. Gate-blocking. |

**A control in DESIGNED or ABSENT state does not pass the gate.** The compliance gate is 100% —
*every applicable control must be DEMONSTRATED* before a story reaches Ready for Deploy.

### Verified state of the code as of this baseline (2026-07-27)

- **SCRUM-13 / 14 / 15 / 19 are all in Jira status `To Do` (`stage-todo`).** No `govern/`, `auth/`,
  `connections/`, or `report/` application package exists on any branch. There is **no approval-gate code,
  no RBAC enforcement code, no secret-store implementation, no report code** to test.
- The only governance-relevant code is:
  - **PR #1 (merged):** ingest connectors + `Signal` store. Persists `actor` (Jira `assignee.displayName` = PII).
    `POST /projects/{id}/ingest` has **no authentication**.
  - **PR #7 (unmerged proposal, data-layer only):** ORM models + 8 Alembic migrations — the `audit_log`
    append-only trigger (0007), RLS policies (0008, **Postgres-only, never executed against Postgres**),
    `users`/`roles`, `connections.credential_ref`, `actions`/`approvals`. No endpoints, no services, no
    RLS session wiring, no secret-store behind `credential_ref`.

**Consequence:** the gate outcome for all four stories is **NO-GO** today (see §6). This matrix defines the
controls each story must DEMONSTRATE to flip to GO.

---

## 1. Framework applicability

| Framework | Applies because | Note |
|---|---|---|
| **SOC 2** (Trust Services Criteria, CC series) | The product's differentiator is *governed, auditable AI action* — access control (CC6), change accountability (CC8.1), and monitoring (CC7) are the core sell. | In scope for the whole platform. |
| **GDPR** | Ingested delivery data contains **personal data** — Jira assignee/reporter display names, GitHub logins (`actor`), and platform user accounts. | In scope now (PII is already ingested by merged code). |
| **HIPAA** | The platform ingests **no PHI today**. HIPAA (45 CFR §164.312 Security Rule) applies **only if** a customer connects a source containing PHI. | **Conditional.** The data-classification rules (`data-classification.md`) MUST prevent PHI from silently entering via SCRUM-19 connections without a HIPAA control uplift. Tracked as a gate condition on SCRUM-19. |

---

## 2. Audit-log immutability & retention (SCRUM-13)

| # | Requirement | Framework | How satisfied (design) | Evidence artifact | State | Gap / Owner |
|---|---|---|---|---|---|---|
| A1 | Audit entries are **immutable** — UPDATE/DELETE rejected at the data layer | SOC 2 CC7.2/CC8.1; GDPR Art 32(1)(b); HIPAA §164.312(c)(1), §164.312(b) | `BEFORE UPDATE/DELETE` trigger raising on any mutation, Postgres + SQLite (`migrations/0007_audit_log.py`); Postgres `REVOKE UPDATE,DELETE` from `delivery_app` (0008) | `0007_audit_log.py` trigger; `tests/test_audit_log_immutability.py` (per `docs/db/schema.md`) exercises the real trigger on SQLite | **DESIGNED** | Trigger is on an **unmerged** proposal branch; the 0008 REVOKE is **never executed against Postgres**. Need: merge + a DEMONSTRATED negative test (update/delete → rejected) on the deploy DB engine. Owner: developer + dba + devops |
| A2 | One immutable entry **per executed step** capturing **actor(agent), approver identity, timestamp, operation, target, evidence signal IDs, adapter response** | SOC 2 CC8.1; GDPR Art 30; HIPAA §164.312(b) | `AuditLog` columns: `event_type, actor_type, actor_label, action_id, target_ref, evidence_signal_ids, payload, occurred_at`; approver captured via linked `approvals` row + `payload` | `audit_log.py` ORM; `approval.py` ORM (`approver_label` never generic) | **DESIGNED** | The schema **does not structurally force** the approver onto an `EXECUTION` row — it relies on the SCRUM-13 implementation writing actor(agent) + approver(from `approvals`) in the **same transaction**. No such code exists. Owner: developer (write-path); compliance verifies |
| A3 | Every loop **stage** writes an audit entry (DETECTION, PROPOSED, APPROVAL, EXECUTION, REJECTION, EDIT, DENIED) — a completed run holds **both** a detection and an action record | SOC 2 CC7.2; GDPR Art 5(2) accountability | `event_type` free-text vocabulary; `AuditService.append` is sole writer (architecture §6); Detect has a `NullAuditSink` seam to wire in | `docs/ARCHITECTURE.md` §3/§6; `docs/db/schema.md` event vocabulary | **DESIGNED** | `AuditService` not built; Detect currently writes to a **no-op** sink. Need DEMONSTRATED: audit query after an E2E run shows DETECTION + EXECUTION. Owner: developer; qa verifies (AC-GOVERN) |
| A4 | Audit entries are **attributable to a real identity, never generic/system** | SOC 2 CC6.1; HIPAA §164.312(d); GDPR Art 5(2) | `approver_label` non-null, carried independently of `approver_id` (survives account deletion); `actor_type in ('user','agent','system')` CHECK | `approval.py`, `audit_log.py` ORM + `ck_audit_actor_type` | **DESIGNED** | Enforcement that an approval EXECUTION never records `system` as approver is app-layer; needs the SCRUM-14 identity binding + a denied-path test. Owner: developer + security |
| A5 | Audit log is **queryable** chronologically per tenant | SOC 2 CC7.2; HIPAA §164.312(b) | `GET /projects/{id}/audit`; `(organization_id, occurred_at)` composite index | architecture §5.6; `schema.md` index plan | **DESIGNED** | Endpoint not built. Owner: developer |
| A6 | **Retention** of audit records is defined, enforced, and ≥ the regulatory floor | SOC 2 CC7.2 / A1.1; GDPR Art 5(1)(e) storage limitation; HIPAA §164.316(b)(2) (6-year retention) | **NOT DESIGNED.** `schema.md` explicitly **defers** partitioning/retention ("revisit when devops has real retention numbers") | — | **ABSENT** | **Compliance-owned gap.** Retention policy defined below (§2.1); must be implemented + evidenced before SCRUM-13 deploys. Owner: compliance (policy) → dba/devops (enforcement) |
| A7 | Audit records containing PII are **reconciled with the GDPR erasure path** (immutable log vs right-to-erasure) | GDPR Art 17(1) vs 17(3)(b)/(e) | **NOT DESIGNED** | — | **ABSENT** | See `data-classification.md` §4. Audit PII retained under legal-obligation/legitimate-interest exemption; erasure targets operational stores, not the immutable log; pseudonymize actor labels where feasible. Owner: compliance |

### 2.1 Audit retention policy (Compliance-defined — fills gap A6)

- **Minimum retention:** **6 years** from entry creation, to satisfy the HIPAA §164.316(b)(2) floor and give a
  single conservative rule that also covers SOC 2 evidence-retention expectations. Applies whether or not PHI is
  present (single policy avoids misclassification risk).
- **Immutability during retention:** no UPDATE/DELETE (control A1). Deletion is permitted **only** on expiry of the
  retention window, via a controlled, audited purge job — never ad hoc.
- **Storage-limitation reconciliation (GDPR Art 5(1)(e)):** the 6-year retention is the defined, documented limit;
  it is a *maximum and a minimum*. Purge on expiry is mandatory, not optional, so the log is not kept indefinitely.
- **Erasure reconciliation (A7):** audit rows are exempt from erasure under GDPR Art 17(3)(b)/(e) (legal obligation /
  establishment of legal claims). The erasure path operates on `Signal.actor`, `User` PII, and secret material —
  not on the immutable audit trail. This exemption must be recorded in the Art 30 processing record.

---

## 3. RBAC / approver accountability (SCRUM-14)

| # | Requirement | Framework | How satisfied (design) | Evidence artifact | State | Gap / Owner |
|---|---|---|---|---|---|---|
| R1 | Authorization on approve/reject/edit enforced **server-side** (hiding UI is not a control) | SOC 2 CC6.1/CC6.3; HIPAA §164.312(a)(1); GDPR Art 32 | `require_role("approver")` FastAPI dep on approve/reject/edit (architecture §5.5); `rbac.md` §3 | `docs/security/rbac.md`; architecture §5.6 | **DESIGNED** | `auth/` package not built. Need DEMONSTRATED denied-path test (viewer → 403, zero adapter calls, audit entry). Owner: developer + security |
| R2 | **Least-privilege roles** — `viewer` / `approver` / `admin`; capability `action.approve` checked explicitly, not inferred by rank | SOC 2 CC6.1/CC6.3 | `roles` table seeded (migration 0004); `UserRole` join; capability check per action | `user.py` ORM; `0004_users_roles.py`; `rbac.md` §1–2 | **DESIGNED** | Roles seeded in unmerged proposal; no enforcement code. Owner: developer |
| R3 | Unauthorized/viewer approval attempt → **403 + written to immutable audit** | SOC 2 CC6.1/CC7.2; HIPAA §164.312(b) | `DENIED` audit entry on 403 (SCRUM-13 + SCRUM-14 tie); `auth.unauthorized_approval_attempt` event type | `rbac.md` §5; `schema.md` event vocabulary | **DESIGNED** | Depends on both auth + audit code. Owner: developer; security + compliance verify |
| R4 | Unauthenticated caller on any non-`/health` route → **401**; invalid login denied **without disclosing which factor failed** | SOC 2 CC6.1; HIPAA §164.312(d); GDPR Art 32 | `get_current_user` dep on all protected routers; generic 401 (architecture §5.5; `rbac.md` §4) | `rbac.md` §4 | **DESIGNED** | **Merged code violates this today** — `POST /projects/{id}/ingest` has no auth (threat-model I-3). Blocker B2 (§5). Owner: developer + security |
| R5 | Recorded approver = the **real authenticated identity**, never `system`/agent/shared | SOC 2 CC6.1; HIPAA §164.312(d); GDPR Art 5(2) | Session carries `sub, org_id, role`; approver bound from session (`rbac.md` §3 rule 3) | `rbac.md` §3 | **DESIGNED** | Ties to A4. Owner: developer |
| R6 | Role check **and** tenant check both required (either failing = deny); cross-tenant approve/read denied | SOC 2 CC6.1; GDPR Art 32; HIPAA §164.312(a) | Tenant-scoped load + RLS predicate (`rbac.md` §2; `schema.md` RLS plan) | `rbac.md` §2; `0008_rls_policies.py` | **DESIGNED** | RLS never run against Postgres; app-side `SET LOCAL app.current_org_id` wiring **does not exist**. DEMONSTRATED cross-tenant denial test required. Owner: developer + dba + security |
| R7 | No hardcoded secrets; no passwords/tokens in logs | SOC 2 CC6.6; GDPR Art 32; HIPAA §164.312(a)(2)(iv) | JWT secret via settings/secret store; bcrypt; secret scan gate | `secret-handling.md`; `.gitleaks.toml` CI | **DESIGNED** (config pattern present in PR #1) | Verify at SCRUM-14 code review + clean gitleaks run. Owner: security |

---

## 4. PII handling — `actor` = Jira `assignee.displayName` (SCRUM-7) & data minimization

**This is the one PII control area that touches *merged, live* code — it is a blocker, not a future story.**

| # | Requirement | Framework | How satisfied (design) | Evidence artifact | State | Gap / Owner |
|---|---|---|---|---|---|---|
| P1 | Personal data ingested by connectors is **classified** and its handling rules defined | GDPR Art 30, Art 5(1); SOC 2 CC1/CC3 | `data-classification.md` classifies `Signal.actor` (Jira `assignee.displayName`, GitHub login) as **Personal / Restricted-PII** | `docs/compliance/data-classification.md` | **DESIGNED** (this PR) | Classification now exists; enforcement (below) does not. Owner: compliance (done) → developer (enforce) |
| P2 | **Data minimization** — store only the personal data a story needs; never persist source emails | GDPR Art 5(1)(c), Art 25(2); SOC 2 CC3 | Connectors store `displayName`/`login` only; `reporter.emailAddress` is **not** persisted (verified in `jira.py` — only `assignee.displayName` read) | PR #1 `connectors/jira.py` (no email field read) | **DEMONSTRATED (partial)** | Good: emails are not ingested. Gap: `displayName` is stored with **no lawful-basis record, no retention limit, no erasure path**. Owner: developer + compliance |
| P3 | **Lawful basis / records of processing** for ingested PII | GDPR Art 6, Art 30 | **NOT DESIGNED** | — | **ABSENT** | Art 30 record must name: controller (customer org), processor (platform), purpose (delivery-risk detection), categories (display names/logins), retention. Owner: compliance |
| P4 | **Right-to-erasure path** for operational PII (`Signal.actor`, `User`) | GDPR Art 17 | **NOT DESIGNED** | — | **ABSENT** | Erasure/pseudonymization procedure for `Signal.actor` + user records, reconciled with immutable audit (A7). Owner: compliance → developer |
| P5 | PII not written to logs; raw source payloads not logged | GDPR Art 32; SOC 2 CC6.6; HIPAA §164.312(b) | threat-model I-5 control (do not log raw payloads/URLs) | `threat-model.md` §1 I-5 | **DESIGNED** | No structured-logging redaction code exists yet. Verify at SCRUM-19/live-connector review. Owner: developer + security |
| P6 | PII reaching the **LLM** is bounded to low-sensitivity evidence; no secrets/descriptions/comments | GDPR Art 5(1)(c), Art 25; SOC 2 CC6.1 | Prompt carries only keys/dates/states/labels + already-stored actor names; citations computed from data (architecture §7) | architecture §7 "Security note" | **DESIGNED** | Egress payload review required at SCRUM-11 (Explain). Owner: security + compliance |
| P7 | Classification **drives what may reach models and logs** (esp. blocking PHI) | HIPAA §164.312; GDPR Art 25 | `data-classification.md` tiers gate egress; PHI tier = do-not-ingest without HIPAA uplift | `data-classification.md` §2–3 | **DESIGNED** | Enforcement point (a classification check at the connection/ingest boundary) not built. Owner: developer + compliance |

---

## 5. Credential data-classification for the connections store (SCRUM-19)

| # | Requirement | Framework | How satisfied (design) | Evidence artifact | State | Gap / Owner |
|---|---|---|---|---|---|---|
| C1 | Customer credentials classified **highest sensitivity (Secret)**; handling rules defined | SOC 2 CC6.1/CC6.6; GDPR Art 32; HIPAA §164.312(a)(2)(iv) | `data-classification.md` §2 Tier 4 (Secret) — credentials, never logged/returned/stored plaintext | `data-classification.md` §2 | **DESIGNED** (this PR) | Classification exists; secret store impl does not. Owner: compliance (done) → developer |
| C2 | **No plaintext credentials** in DB rows, tickets, or logs | SOC 2 CC6.6; GDPR Art 32; HIPAA §164.312(a)(2)(iv) | `Connection` has **no credential column** — only `credential_ref` opaque pointer (migration 0005; `connection.py`) | `connection.py` ORM; `0005_connections.py`; `secret-handling.md` S-3 | **DESIGNED** | The `SecretStore`/`EnvelopeSecretStore` behind the pointer **does not exist**. Owner: developer + security |
| C3 | Credentials **write-only across the API** — never returned on read | SOC 2 CC6.1; GDPR Art 32; HIPAA §164.312(a) | Read schema excludes secret; `credential_ref` never echoed (`secret-handling.md` S-4) | `secret-handling.md` §3; `connection.py` docstring | **DESIGNED** | No API exists; readback-masking test required. Owner: developer + security |
| C4 | **Tenant isolation** — one org never resolves another's connection/data/audit | SOC 2 CC6.1; GDPR Art 32; HIPAA §164.312(a)(1) | `organization_id` on every tenant table + Postgres RLS, fail-closed on unset session var (0008; `schema.md` RLS plan) | `0008_rls_policies.py`; `schema.md` | **DESIGNED** | **Never executed against Postgres**; `SET LOCAL app.current_org_id` app wiring absent; `user_roles` has **no RLS policy**. DEMONSTRATED cross-tenant denial test required. Owner: dba + developer + security |
| C5 | **SSRF guard** on customer `base_url` (https-only; reject link-local/loopback/RFC-1918/metadata; resolve-then-pin) | SOC 2 CC6.1; GDPR Art 32 | threat-model I-4 control | `threat-model.md` §1 I-4 | **ABSENT** (no code) | Compliance exposure: unauthorized data access. Owner: developer + security |
| C6 | **Disable/delete stops ingest immediately and purges secret material** (no cached copies) | SOC 2 CC6.1; GDPR Art 17/Art 5(1)(e); HIPAA §164.310(d)(2)(i) | `ConnectionService.delete` purges via `SecretStore.delete` (architecture §8; `secret-handling.md` §4) | `secret-handling.md` §4 | **DESIGNED** | No service code. Owner: developer |
| C7 | `Test connection` returns a **non-sensitive** result; never echoes raw upstream 401 body | SOC 2 CC6.6; GDPR Art 32 | Error mapped to generic message; `last_test_message` "non-sensitive only" (app-layer promise) | `secret-handling.md` §5; `connection.py` docstring | **DESIGNED** | Error-shaping code must be security-reviewed. Owner: developer + security |
| C8 | **Least-privilege scopes** on stored tokens (read-only for ingest); flag over-broad grants | SOC 2 CC6.1; HIPAA §164.312(a)(1) | Documented scopes + validate at Test connection (`secret-handling.md` S-5) | `secret-handling.md` §1 | **DESIGNED** | Owner: developer + security |
| C9 | **PHI containment** — a connected source must not silently introduce PHI without a HIPAA uplift | HIPAA §164.308/§164.312; GDPR Art 9 (special categories) | `data-classification.md` PHI tier: connections default to non-PHI; PHI requires explicit control uplift + BAA | `data-classification.md` §3 | **DESIGNED** | Enforcement/attestation at connection creation not built. Owner: compliance + developer |

---

## 6. Gate conditions — what must be TRUE before Ready for Deploy (100% gate)

The compliance gate is **100%: every applicable control DEMONSTRATED**. Per the Jira workflow, a fail returns the
story to **In Progress + Developer** with the named control gap; a pass co-signed with Security moves
`stage-security → stage-deploy`.

### SCRUM-13 (approval + immutable audit) — **GO requires ALL of:**
1. A1 DEMONSTRATED: update/delete of an `audit_log` row is **rejected** — negative test passing against the
   **deploy DB engine** (Postgres), not only SQLite.
2. A2 + A4 DEMONSTRATED: an executed step writes **one** audit entry with actor(agent) **and** real approver
   identity, timestamp, operation, target, evidence signal IDs, adapter response — verified by test.
3. A3 DEMONSTRATED: after an E2E run the audit query returns **both** a DETECTION and an EXECUTION record.
4. Edit/reject integrity DEMONSTRATED: reject → zero adapter calls + reason recorded; edit → only edited steps run;
   both versions recorded.
5. **A6 retention** implemented + evidenced (6-year floor, controlled purge) and **A7 erasure reconciliation**
   recorded in the Art 30 register.
6. Co-review with Security passes (kill-switch, `DENIED` path, adapter-boundary A-1).

### SCRUM-14 (auth/RBAC) — **GO requires ALL of:**
1. R1 + R3 DEMONSTRATED: viewer calling approve/reject/edit → **403, zero adapter calls, audit entry written**.
2. R4 DEMONSTRATED: unauthenticated call to every protected route → 401; invalid login → generic denial.
3. R5 DEMONSTRATED: approved action records the **real** approver identity (never generic/system).
4. R6 DEMONSTRATED: cross-tenant approve/read → denied (RLS + tenant check), run against Postgres.
5. R7: clean gitleaks run; no tokens/passwords in logs (code review).

### SCRUM-19 (connections / credentials) — **GO requires ALL of:**
1. C2 + C3 DEMONSTRATED: credential stored only as a reference (secret store / envelope-encrypted), **never**
   returned on any read — readback-masking test passing.
2. C4 DEMONSTRATED: cross-tenant connection resolution **denied** — negative test against Postgres; `user_roles`
   RLS gap closed or explicitly risk-accepted by Security.
3. C5 DEMONSTRATED: SSRF guard on `base_url` rejects link-local/loopback/RFC-1918/metadata hosts.
4. C6 DEMONSTRATED: disable/delete stops ingest and purges secret material.
5. C7 DEMONSTRATED: Test connection returns non-sensitive errors only.
6. C9: connection-creation records a non-PHI attestation (or triggers the HIPAA uplift path).
7. Data-classification entry for stored credentials (this PR) confirmed against the built behavior.

### SCRUM-15 (executive report) — **GO requires:**
- Report is **read-only over persisted stage outputs** and introduces **no new data class** — confirm at review it
  surfaces only already-classified, non-sensitive fields (health, risk, top citation, approver name) and **no
  secrets, no raw PII beyond the approver display name already governed under A4/P1**.
- Pending-state honesty (never claims action taken while `PENDING_APPROVAL`) — reportable, not a data-handling gate.
- SCRUM-15 carries **no independent audit/RBAC/PII control of its own** beyond inheriting SCRUM-14 auth on
  `GET /runs/{run_id}/summary`. Its gate is **conditional on SCRUM-13/14 passing** (it displays their governed data).

---

## 7. Blockers on merged / foundation code

These are **live gaps on merged code (PR #1)**, independent of the unbuilt stories. They are flagged to the
`developer`/`security` owners and tracked on the relevant tickets.

| ID | Blocker | Framework exposure | Where | Owner ticket |
|---|---|---|---|---|
| **B1** | **PII ingested with no classification, no lawful-basis record, no retention limit, no erasure path.** `Signal.actor` stores Jira `assignee.displayName` (personal data) on the merged ingest path. | GDPR Art 5(1)(c)/(e), Art 6, Art 17, Art 30 | PR #1 `connectors/jira.py`, `ingest/service.py`, `models/signal.py` | SCRUM-7 (extend); enforced via SCRUM-19 data-classification |
| **B2** | **Unauthenticated ingest.** `POST /projects/{id}/ingest` has no auth dependency — unauthorized data-processing endpoint. | SOC 2 CC6.1; GDPR Art 32; threat-model I-3 | PR #1 `api/ingest.py` | SCRUM-14 |
| **B3** | **JQL injection (I-1) / repo path-SSRF (I-2)** on live gateways — enables cross-project/cross-tenant data access. | SOC 2 CC6.1; GDPR Art 32 | PR #1 `connectors/jira.py`, `connectors/github.py` | SCRUM-19 (pre-live), security-owned |

**These blockers do not block this documentation PR** — they block the *features* going live and are named here so
no story ships past them. Per the guardrail **don't ship past a control gap**, B1–B3 must be closed on their owning
stories before those stories reach Ready for Deploy.

---

## 8. Verification note

This matrix is **verified against real artifacts**: Jira ticket statuses (all four `stage-todo`), PR #1 merged code,
PR #7 unmerged data-layer proposal, and the security baseline docs. No control is marked DEMONSTRATED without a
traceable test/behavior. The append-only trigger (A1) and credential-reference model (C2) are the strongest DESIGNED
controls but remain unmerged and unproven against Postgres — they are **designed for, not demonstrated**, and
therefore do not pass the gate yet.
