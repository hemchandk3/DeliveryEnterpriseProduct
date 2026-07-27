# Secret & Credential Handling (MVP) — SCRUM-19

**Owner:** Security. **Story:** SCRUM-19 (S13 — configure an organization's own data-source connection).
**Rule of the platform:** no plaintext secrets, scoped tokens, rotatable, never logged, never returned on read.

Two classes of secret exist:
1. **Platform secrets** — the app's own config (DB URL, the demo `GITHUB_TOKEN`/`JIRA_TOKEN` in `.env`).
2. **Customer credentials** — per-organization source tokens supplied through the connections story (SCRUM-19). Highest sensitivity: a leak exposes a customer's Jira/GitHub.

---

## 1. Hard rules (release-blocking)

| # | Rule | Enforcement |
|---|------|-------------|
| S-1 | **No secret in source control.** No tokens, passwords, keys, or `.env` files committed. | `.gitleaks.toml` + `scripts/security_scan.sh` in CI (`.github/workflows/security.yml`). Any hit = merge blocked. |
| S-2 | **No secret in logs or errors.** No token, password, Authorization header, or raw upstream auth-error body written to logs / traces / API responses. | Code review + scan; structured logging must redact; connectors must not log raw payloads or full request URLs. |
| S-3 | **No secret in the DB in plaintext.** Customer credentials never stored as a plaintext column, and never in a Jira ticket. | Secret store or envelope-encrypted column (§3). |
| S-4 | **Write-only across the API.** Credentials accepted on write; **never** returned on any read (masked/omitted). | Response schema excludes the secret field; readback test asserts masking. |
| S-5 | **Scoped + least privilege.** Request the minimum scope (read-only for ingest); reject/flag over-broad grants. | Documented scopes + `Test connection` validation. |
| S-6 | **Rotatable + revocable.** A credential can be replaced or deleted without code changes; disable/delete removes stored material and stops ingest. | Connection model supports update/delete of secret; no cached copies. |

---

## 2. Platform secrets (config)

- Loaded from environment via `pydantic-settings` (`backend/app/config.py`) — already the pattern in PR #1. Good.
- `.env` is git-ignored (`backend/.gitignore`); only `.env.example` with **empty** values is committed. Verified: no populated secrets in the repo at baseline.
- **`.gitignore` hardening:** root `.gitignore` covers `.env`, `*.pem`, `*.key`. Keep `*.db` ignored (SQLite may hold ingested data) — `backend/.gitignore` already does.
- Never widen a token's scope "for convenience." The demo `GITHUB_TOKEN` should be read-only (`contents:read`) for ingest; write scopes for the (mock) Act stage are not required against live systems in the MVP.

## 3. Customer credentials (SCRUM-19) — storage design

**Boundary:** the API accepts a credential on `POST /connections`, hands it straight to the secret store, and keeps only a **reference** (secret id / key path) on the connection row.

**Acceptable stores (in order of preference):**
1. A managed secret manager (e.g. cloud KMS-backed secrets) — connection row stores only the secret reference.
2. If stored in Postgres for the MVP: **envelope encryption** — column encrypted with a data key wrapped by a KMS master key; the master key never lives in the DB or the repo. Plaintext columns are not acceptable.

**Non-negotiables:**
- The connection row carries: tenant id, source type, instance URL, target project/repo, secret **reference** — **not** the secret.
- Read paths (`GET /connections`, list, audit, logs) return the connection with the credential **masked/omitted** (S-4).
- Decryption happens only in the ingest worker, at call time, in memory; plaintext is never persisted, logged, or returned.
- Tenant-scoped: a connection (and its secret reference) is only resolvable within its owning organization (threat-model C-3; DBA owns RLS).

## 4. Rotation & revocation (S-6)

- **Rotate:** admin submits a new credential → new secret version written, old version destroyed after cutover. No redeploy needed.
- **Revoke/disable:** disable stops ingest immediately; delete removes secret material and the reference. No cached token survives in memory beyond the run.
- Automated/scheduled rotation is roadmap (SCRUM-19 out-of-scope) — but the model must not **prevent** rotation (no secret baked into code/config requiring a deploy to change).

## 5. `Test connection` safety (SCRUM-19)

- Makes a real, **read-only** call to the source and reports success or a **clear, non-sensitive** error.
- Never echo the raw upstream 401/403 body (may contain token fragments) — map to a generic "authentication failed / check credentials and scopes."
- The credential used for the test comes from the secret store, not the request echo.

## 6. Baseline check (run at review time)
```
bash scripts/security_scan.sh          # gitleaks (secrets) + pip-audit (deps)
```
`scripts/security_scan.sh` is the local mirror of the CI gate; a clean run is required before a security pass. See `dependency-scanning.md` for the dependency half.

## 7. Evidence for Compliance
This document + a clean `gitleaks` run + the SCRUM-19 tests (credential masked on read, encrypted at rest, removed on delete, cross-tenant denied) are the control evidence for the "stored customer credentials" data-classification entry. Handed to `compliance`.
