# RBAC & Authorization Model (MVP) — SCRUM-14

**Owner:** Security. **Story:** SCRUM-14 (S8 — Authenticate users and restrict approval to approver role).
**Principle:** least privilege, fail closed, enforced **server-side**. Hiding a UI button is not authorization.

The MVP has one consequential capability — **approving an agent action at the Govern gate** — and it must be restricted to the approver role. Everything else is read/observe.

---

## 1. Roles

| Role | Intent | Who |
|------|--------|-----|
| `viewer` | Read delivery health, risks, explanations, audit log. Cannot approve. | Team members, execs (read-only). |
| `approver` | Everything a viewer can do **plus** approve / reject / edit an agent action at the Govern gate. | The PM who owns the delivery outcome. |
| `admin` | Everything an approver can do **plus** manage data-source connections (add/test/enable/disable — SCRUM-19). | Org onboarding owner. |

MVP keeps the set intentionally small (workstream §5.3 assumes a single PM approver). `admin ⊇ approver ⊇ viewer` in read scope, but **capabilities are checked explicitly per action**, not inferred from a rank order — so a future non-hierarchical role does not silently inherit approval rights.

Out of scope (roadmap): SSO/SAML, self-signup, multi-tier approval, delegation, per-project role assignment.

---

## 2. Permission matrix

| Capability | viewer | approver | admin |
|------------|:------:|:--------:|:-----:|
| View detection / explanation / report | ✅ | ✅ | ✅ |
| View audit log | ✅ | ✅ | ✅ |
| Trigger ingest (`POST /projects/{id}/ingest`) | ❌ | ✅ | ✅ |
| **Approve / reject / edit agent action** | ❌ | ✅ | ✅ |
| Manage connections & credentials (SCRUM-19) | ❌ | ❌ | ✅ |

Every capability is **tenant-scoped**: a subject may only act on resources belonging to its own organization (threat-model §4, C-3). Role check and tenant check are **both** required; either failing = deny.

---

## 3. The approver-only approval model (the load-bearing control)

The Govern gate (SCRUM-13) is where an agent proposal can become a real, team-visible action. Authorization here is the difference between "governed" and "ungoverned".

**Rules (all server-side, all fail-closed):**

1. **Authentication first.** `approve`, `reject`, `edit` require a valid session/token carrying subject identity + role. No session → `401`, no execution, audit-logged as an unauthenticated attempt.
2. **Approver (or admin) only.** The handler checks capability `action.approve` before doing anything else. A `viewer` → `403`, **zero** adapter calls, and the refused attempt is **written to the immutable audit log** (SCRUM-13 AC: "unauthorised approval attempt → refused and audit-logged").
3. **Identity is real, never generic.** The approver recorded in the audit entry is the authenticated subject — never `system`, never the agent, never a shared account (threat-model G-3/G-5).
4. **Decision drives execution, exclusively.** Adapters execute only on transition to `APPROVED` by an authorized approver. `reject` → nothing executes, reason recorded. `edit` → only edited/approved steps execute; original + edited versions recorded.
5. **No client-side trust.** The frontend reads the subject's role only to **show/hide** approval controls (usability). The server re-checks on every request; a hand-crafted call from a viewer session is refused regardless of the UI.

### Denied-path pseudocode (enforcement point)
```
def approve_action(action_id, subject):
    require_authenticated(subject)                 # else 401 + audit(unauthenticated)
    action = load_action(action_id, tenant=subject.tenant)  # tenant-scoped; else 404
    if not subject.has_capability("action.approve"):        # viewer, etc.
        audit.append(kind="approval_denied", subject=subject, action=action_id)
        raise Forbidden()                          # 403, zero adapter calls
    execute_approved_steps(action, approver=subject.identity)  # real identity
    audit.append(kind="approval_executed", approver=subject.identity, ...)
```

---

## 4. Authentication requirements (SCRUM-14 acceptance)

- Valid credentials → session/token carries identity **and** role.
- Invalid credentials → access denied **without revealing which factor failed** (no "user exists / wrong password" distinction; generic error).
- Unauthenticated caller on detection / explanation / action / audit / report / ingest → refused (`401`). Only `GET /health` is public.
- Frontend can read identity/role to show/hide approval controls — **display only**, never the enforcement point.
- No hardcoded secrets; no passwords or tokens in logs (verified by secret scan + code review). See `secret-handling.md`.

---

## 5. Verification (what Security tests before passing SCRUM-13/14)

Authorization is verified by exercising **denied** cases, not just happy paths:

- [ ] Viewer calls `approve` / `reject` / `edit` directly → `403`, zero adapter calls, **audit entry written**.
- [ ] Unauthenticated call to each protected route → `401`, no state change.
- [ ] Invalid login → denied without disclosing which factor failed.
- [ ] Approved action → audit records the **real approver identity**, never generic/system.
- [ ] Cross-tenant: subject in Org A cannot approve/read Org B's action → `404`/`403`.
- [ ] Frontend hides approval controls for viewer, **and** server still refuses a forged viewer request (defense in depth).

## 6. Evidence for Compliance
Test output for the checklist above + this document map SCRUM-14 to SOC 2 access-control / least-privilege criteria and the GDPR "authorized processing" expectation. Handed to `compliance` for control mapping.
