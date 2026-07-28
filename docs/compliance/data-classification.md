# Data Classification & Handling — MVP

**Owner:** Compliance. **Status:** Baseline for the 100% compliance gate.
**Purpose:** classify **every** data element the platform ingests or stores, and pin the handling rule per tier —
so classification (not code convenience) governs what may reach models, logs, reads, and other tenants.
**Companion:** `docs/compliance/control-matrix.md` (controls + gate conditions).

Classification is **privacy-by-default**: if an element's tier is unclear, treat it as the **more** restrictive tier
until Compliance rules otherwise.

---

## 1. Classification tiers

| Tier | Name | Definition | Default handling posture |
|---|---|---|---|
| **T1** | **Public / Non-sensitive** | Operational metadata with no personal or confidential content. | May be stored, logged, displayed, and sent to the LLM. |
| **T2** | **Internal** | Business/delivery data that is not personal but is customer-confidential (tenant-scoped). | Store + display tenant-scoped; may reach LLM as evidence; **not** logged in raw payload form. |
| **T3** | **Personal / Restricted-PII** | Data identifying a person (names, usernames, emails). Special categories (GDPR Art 9) / PHI escalate to the HIPAA posture (§3). | Minimize; tenant-scoped; **never in logs**; erasable; only the minimum reaches the LLM. Lawful basis + Art 30 record required. |
| **T4** | **Secret** | Credentials, tokens, keys, password hashes. A leak compromises a customer system or account. | **Never** plaintext in DB/logs/tickets/API reads. Write-only; encrypted at rest; reference-only; least privilege. |

**PHI overlay (conditional):** any T2/T3 element sourced from a connection that carries **Protected Health
Information** is handled under the **HIPAA posture (§3)** regardless of its base tier. The MVP ingests no PHI; the
overlay exists so a future connection cannot silently bypass it.

---

## 2. Element inventory — every ingested/stored data element

### 2.1 Ingested delivery signals (`Signal`, from Jira/GitHub)

| Element | Source field | Tier | Handling rule |
|---|---|---|---|
| Issue/PR/commit/sprint key, `external_id` | `key`, PR `number`, commit `sha`, sprint `id` | **T1** | Store, display, cite, LLM-OK. |
| Title / summary | `fields.summary`, PR `title`, commit message first line | **T2** | Store + cite; may reach LLM as delimited evidence (treat as untrusted per threat-model I-6/A-2). Not logged raw. |
| State / status | `status.name`, PR `state`, `draft` | **T1** | Store, display, cite, LLM-OK. |
| **`actor` (assignee/author display name or login)** | Jira `assignee.displayName`; GitHub `user.login` / commit `author.login` | **T3** | **Personal data.** Minimize (display name/login only — see 2.5). Tenant-scoped. Never in logs. Erasable (§4). Only the name reaches the LLM, and only as evidence attribution. **This is the SCRUM-7 PII element flagged in the control matrix (B1).** |
| Priority, labels, story points | `priority.name`, `labels`, `customfield_10016` | **T2** | Store + cite; LLM-OK as evidence. |
| Issue links / blockers | `issuelinks[]` | **T2** | Store + cite; LLM-OK. May transitively name other issues (T1 keys). |
| Timestamps | `created`, `updated`, `author.date` | **T1** | Store, display, cite, LLM-OK. |
| PR review/reviewer state | `reviews[].state`, `requested_reviewers[]` (logins) | **T3** (login is personal) | Reviewer **login** is personal data → same rule as `actor`. Review *state* alone is T2. |
| Sprint goal | `sprint.goal` | **T2** | Store + cite; LLM-OK. |
| `meta` blob (schemaless) | assembled | **inherits highest tier of contents** | Because `meta` can carry logins/labels, classify as **T3** in aggregate; never log raw. |

> **Explicitly NOT ingested (minimization, GDPR Art 5(1)(c)):** Jira reporter `emailAddress`, issue descriptions,
> and comment bodies. Verified in PR #1 `connectors/jira.py` — only `assignee.displayName` is read. Keep it that
> way: source emails and free-text bodies must **not** be persisted in `meta`.

### 2.2 Platform user accounts (`User`, SCRUM-14)

| Element | Tier | Handling rule |
|---|---|---|
| `email` | **T3** | Personal data. Tenant-scoped; unique per org; normalized lowercase. Erasable (§4). Never logged. |
| `display_name` | **T3** | Personal data. Same rule. |
| `hashed_password` | **T4** | Secret. bcrypt/argon2 hash only, never plaintext, never logged, never returned on read. |
| `role` / `UserRole` | **T2** | Authorization metadata; tenant-scoped. |
| `is_active`, timestamps | **T1** | Operational. |

### 2.3 Connections & credentials (`Connection`, SCRUM-19)

| Element | Tier | Handling rule |
|---|---|---|
| **Customer source credential** (Jira token, GitHub PAT) | **T4** | **Highest sensitivity.** Never stored in a DB column — only a `credential_ref` pointer to a secret store / envelope-encrypted blob. Write-only across the API; never returned on read; never in logs, tickets, or `Test connection` errors. Least-privilege scopes. Purged on disable/delete. |
| `credential_ref` | **T2** | Opaque pointer (e.g. vault path/ARN). Not itself a secret, but tenant-scoped and not user-facing. |
| `instance_url` (`base_url`) | **T2** | Customer-confidential; SSRF-validated before use (control C5). |
| `target_ref` (repo / project key) | **T2** | Tenant-scoped. |
| `last_test_message` | **T1** (must be non-sensitive) | Generic status only; **must never** contain raw upstream auth-error bodies or credential fragments (control C7). |

### 2.4 Governance records (`Action`, `Approval`, `AuditLog`, SCRUM-13)

| Element | Tier | Handling rule |
|---|---|---|
| `actor_label` / `approver_label` | **T3** | Personal data (identifies the agent operator / approving person). Immutable in `audit_log`; **retained under legal-obligation exemption**, not erased (§4). Pseudonymize where operationally feasible. |
| `operation`, `target_ref`, `event_type` | **T1/T2** | Governance metadata; tenant-scoped. |
| `evidence_signal_ids`, `payload` | **inherits** | Classify by contents; `payload` must **not** embed T4 secrets or raw source payloads. |
| `proposed_steps` / `edited_steps` | **T2** | Action content; no secrets. |

### 2.5 Derived / model-facing data (Explain, Report, LLM)

| Element | Tier | Handling rule |
|---|---|---|
| Explanation prose + citations | **T2** | Computed from stored signals; carries T1 keys + T3 actor names as attribution only. |
| **LLM prompt payload** | **bounded to T1/T2 + minimal T3** | Per architecture §7: only keys, dates, states, labels + already-stored actor names. **No T4 secrets, no issue descriptions/comment bodies, no source emails.** Ingested text delivered as delimited, untrusted data (threat-model I-6/A-2). |
| Executive summary (`ExecutiveSummary`) | **T2** | Read-only over persisted outputs; surfaces health/risk/top-citation/approver name only. Introduces **no new data class**. |

---

## 3. HIPAA / PHI posture (conditional)

**The MVP ingests no PHI.** Jira/GitHub delivery metadata for the curated `SCRUM` demo contains none. HIPAA
(45 CFR §164.312 Security Rule) therefore applies **only if** a customer connects a source whose content includes
PHI (or GDPR Art 9 special-category data).

**Containment rules (privacy-by-default):**
1. Connections default to a **non-PHI** classification. Creating a connection records a **non-PHI attestation**
   (control C9). No attestation ⇒ ingest treats the source as potentially PHI-bearing and **blocks** until reviewed.
2. Ingesting PHI requires a **HIPAA control uplift**: a signed BAA with the customer, the audit-controls
   (§164.312(b)) and integrity (§164.312(c)) controls already designed for `audit_log`, transmission security
   (§164.312(e)), and confirmation that no PHI reaches the LLM prompt or logs.
2. Until that uplift exists, **no field classified T2/T3 from a PHI-bearing source may be ingested** — the
   classification check at the connection/ingest boundary is the enforcement point (control P7/C9, owner: developer).

**Where HIPAA already helps us today:** the audit-controls, integrity, access-control, authentication, and
transmission-security requirements the platform builds for SOC 2/GDPR (audit immutability A1–A5, RBAC R1–R7,
credential handling C1–C8) map directly onto §164.312(a)/(b)/(c)/(d)/(e) — so a PHI uplift is an incremental
attestation, not a re-architecture.

---

## 4. Right-to-erasure & retention (GDPR Art 17 / Art 5(1)(e))

Personal data (T3) is erasable; the immutable audit log is the deliberate exception.

| Store | Contains PII | Erasure behavior | Retention |
|---|---|---|---|
| `Signal.actor`, `meta` logins | T3 | On a validated erasure request, **pseudonymize or delete** the personal fields for the data subject. | Retain only while the connection is active + operational need; purge with the connection (C6). |
| `User.email` / `display_name` | T3 | Delete/deactivate; `approver_id` FK is `SET NULL` so audit attribution survives via the label. | Life of the account + defined wind-down. |
| Secret material (T4) | — | Purged on connection disable/delete; no cached copies. | None beyond active use. |
| **`audit_log` (`actor_label`, `approver_label`)** | T3 | **NOT erased.** Exempt under GDPR Art 17(3)(b)/(e) (legal obligation / establishment/defence of legal claims). Pseudonymize labels where feasible without breaking accountability. | **6 years** (HIPAA §164.316(b)(2) floor; also the SOC 2 evidence-retention rule), then controlled, audited purge. |

**Reconciliation statement (must appear in the Art 30 record):** the platform's audit trail is retained immutably
for accountability and legal-claim purposes; erasure requests are honored against operational stores
(`Signal`, `User`, secrets) but **not** the audit log, whose retention rests on a legal-obligation/legitimate-interest
basis. This tension (immutable audit vs erasure) is resolved in favor of the immutability control (A1) with the
narrow, documented Art 17(3) exemption — data subjects are informed of this at collection time (customer-owned notice).

---

## 5. Handling-rule summary (the one-line rules)

1. **Never log** T3 or T4, nor raw source payloads/URLs.
2. **Never return** T4 on any API read; **never store** T4 as plaintext.
3. **Minimize** T3: store the least identifying form needed; do not ingest emails/descriptions/comment bodies.
4. **Tenant-scope** everything T2/T3/T4 — RLS fail-closed; a request that forgets to scope sees zero rows.
5. **LLM egress** is bounded to T1/T2 + minimal T3 attribution; never T4, never free-text bodies.
6. **Erasable** T3 in operational stores; **immutable + 6-yr-retained** T3 in the audit log under the Art 17(3) exemption.
7. **PHI** is out unless a HIPAA uplift + non-PHI-attestation gate is satisfied; unclear tier ⇒ treat as more restrictive.

---

## 6. Enforcement status (privacy by design — not yet privacy by default in code)

Classification is **defined** (this document). Enforcement is largely **not yet built** — the same gap the control
matrix records:

- **DEMONSTRATED:** source emails/descriptions are not ingested (minimization, verified in PR #1 `connectors/jira.py`).
- **DESIGNED (unmerged):** credential reference-only model, audit immutability, RLS tenant scoping (PR #7).
- **ABSENT:** lawful-basis/Art 30 record, erasure procedure, retention/purge job, log-redaction, the
  classification check at the connection/ingest boundary, PHI attestation gate.

Per the guardrail **privacy by default**, the ABSENT items are gate conditions on SCRUM-13/14/19 (see
`control-matrix.md` §6) and the merged-code blocker **B1** on SCRUM-7. This classification must be re-verified
against built behavior — not just intent — before any of those stories passes the 100% compliance gate.
