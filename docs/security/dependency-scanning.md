# Dependency Scanning (MVP)

**Owner:** Security. Part of the ≥ 99% security gate (`docs/ENGINEERING_STANDARDS.md`).
A known-exploitable dependency in a shipped path is a **release blocker**.

## What runs

| Layer | Tool | Command | Blocks on |
|-------|------|---------|-----------|
| Backend (Python) | `pip-audit` | `pip-audit -r backend/requirements.txt` (or `pip-audit --path backend`) | Any advisory with a fix available; unfixed criticals triaged (below). |
| Frontend (Node) | `npm audit` | `npm audit --audit-level=high` | High/critical with a fix. |
| Secrets (all) | `gitleaks` | see `.gitleaks.toml` | Any hit. |

Backend currently declares deps in `backend/pyproject.toml` (fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, httpx). Generate a lockfile / `requirements.txt` for reproducible scans:
`pip install pip-tools && pip-compile backend/pyproject.toml -o backend/requirements.txt`.

## The ≥ 99% gate, concretely
"Security checks ≥ 99%" is treated as **zero unresolved findings** for the two hard checks (secrets, vulnerable deps), because a single leaked credential or exploitable CVE is a full failure — there is no "99% of a secret." A finding is *resolved* only by: (a) upgrading past it, or (b) a documented, time-boxed accepted-risk entry signed off by Security **and** Compliance when no fix exists and the code path is unreachable in the MVP. Silent skips are not allowed (`ENGINEERING_STANDARDS.md` §3).

## Triage of unfixable advisories
1. Confirm whether the vulnerable code path is reachable in a shipped path (fixtures/tests excepted).
2. If unreachable and no fix exists: record an accepted-risk note (advisory id, reason, expiry ≤ 90 days, re-review owner) in the PR and hand to Compliance.
3. If reachable: **blocked** until upgraded or the dependency is replaced.

## CI
Enforced by `.github/workflows/security.yml` (gitleaks + pip-audit on every PR to `main`). `scripts/security_scan.sh` is the local mirror developers run before requesting a security pass.

## Supply-chain hygiene (baseline expectations)
- Pin versions in a lockfile; review new dependencies before adding (least dependency, prefer well-maintained).
- No install-from-URL / unpinned `@latest` in shipped config.
- Re-run scans on dependency bumps, not only on feature PRs.
