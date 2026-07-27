# QA Test Case Catalog — SCRUM-7 … SCRUM-19

Companion to [`docs/qa/test-plan.md`](./test-plan.md). Every case is Given/When/Then, carries an ID (`TC-<STAGE>-<NN>`), the story it verifies, and the exact AC bullet or messy-edge concern it traces to. Cases marked **[E2E]** are also exercised inside the single demo-critical run (`backend/tests/test_e2e_loop.py`, S12).

Status column values: `PLANNED` (not yet built — this catalog is written ahead of SCRUM-9…19 implementation), `WRITTEN`, `PASS`, `FAIL`. QA updates status as each story lands; a story does not move to `stage-security` while any of its mapped cases are `PLANNED` or `FAIL`.

---

## INGEST — S1 Evidence fields (SCRUM-7), S2 Curated dataset (SCRUM-8)

> See QA's PR #1 review comments on SCRUM-7/SCRUM-8 for current implementation status against these cases — several are already `FAIL` against the ticket's finalized AC (Sprint-in-meta, `head_ref`, review `submitted_at`, live field-name resolution, commit issue-key parsing, test/incident ingestion, the `app/demo/*` loader, and `Signal.provenance` are all gaps as of PR #1).

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-ING-01 | Given the curated Jira/GitHub payloads, When ingest runs for `SCRUM` / `hemchandk3/DeliveryEnterpriseProduct`, Then every issue, sprint, PR, commit persists as a `Signal` keyed by `(project_id, source, kind, external_id)` with core fields populated. | SCRUM-7 (AC-INGEST) | PASS |
| TC-ING-02 | Given a prior ingest, When it re-runs on an updated payload, Then signal count is unchanged and the changed row is updated (idempotent upsert). | SCRUM-7 | PASS |
| TC-ING-03 | Given a Jira issue payload, When ingested, Then `meta` retains `priority`, `labels`, `story_points`, and `issuelinks` (type + counterpart key/status). | SCRUM-7 | PASS |
| TC-ING-04 | Given a Jira issue payload, When ingested, Then `meta.sprint = {id, name, state}` is present on the **issue** signal (not only as a separate `kind="sprint"` signal). | SCRUM-7 | FAIL — not implemented; see PR #1 review |
| TC-ING-05 | Given a GitHub PR payload, When ingested, Then `meta` retains `base_ref`, `head_ref`, `draft`, `requested_reviewers`, and `reviews[]` where each review carries `state` **and** `submitted_at`. | SCRUM-7 | FAIL — `head_ref` and `submitted_at` missing |
| TC-ING-06 | Given live Jira (once OAuth available), When ingest runs, Then Story Points/Sprint field ids resolve by **field name** via `GET /rest/api/3/field`, not a hardcoded/defaulted id. | SCRUM-7 | PLANNED (blocked on OAuth + `JiraFieldResolver`) |
| TC-ING-07 | Given the configured Story Points field name does not resolve on the connected instance, When ingest runs, Then it fails loudly (raises, e.g. `FieldResolutionError`) rather than silently storing `None`. | SCRUM-7 | PLANNED |
| TC-ING-08 | Given a commit message containing `SCRUM-42`, When ingested, Then `meta.issue_keys` includes `"SCRUM-42"`. | SCRUM-7 | FAIL — commit `meta` is always `{}` |
| TC-ING-09 | Given a commit message with no issue key (e.g. "chore: bump deps"), When ingested, Then `meta.issue_keys == []` (no false match, no crash). | SCRUM-7 (messy edge) | PLANNED |
| TC-ING-10 | Given the curated dataset, When ingest completes, Then all 12 issues, 1 sprint, 4 PRs, 5 commits, **3 tests, and 1 incident** are queryable as signals. | SCRUM-7 | FAIL — no test/incident connector exists |
| TC-ING-11 | Given a clean DB, When the demo dataset loads for SCRUM via the demo loader, Then sprint, 12 issues, 4 PRs, 5 commits, 3 tests, 1 incident persist with the exact curated dates. | SCRUM-8 | FAIL — no `app/demo/loader.py` exists; dataset is test-fixture-only |
| TC-ING-12 | Given mock gateways (`MockJiraGateway`/`MockGitHubGateway`), When connectors run against them, Then no connector code change is required versus running against the live `*HttpGateway`s (same Protocol). | SCRUM-8 | PLANNED (Protocol seam exists today via `tests/fakes.py`; named production module does not) |
| TC-ING-13 | Given any ingested signal, When read via the API, Then `provenance` is present and is exactly `"demo"` or `"live"`. | SCRUM-8 | FAIL — `Signal.provenance` column does not exist |
| TC-ING-14 | Given a signal with `provenance="demo"`, When the frontend requests it, Then a "Demo data" indicator is derivable from the response (no client-side guessing). | SCRUM-8 | PLANNED |
| TC-ING-15 | Given the demo loader runs twice in a row, Then no duplicate signals are created (same idempotent upsert key as live ingest). | SCRUM-8 | PLANNED |
| TC-ING-16 | Given the loaded demo dataset, When QA queries SCRUM-42, Then `status="In Progress"`, `updated=2026-07-18`, `priority="Highest"`, `labels` ⊇ `{critical-path, release-1.4}`, and it is "blocked by" SCRUM-45. | SCRUM-8 | PASS (verified via `test_fixtures.py`; not yet reachable via a live loader — see TC-ING-11) |

### Messy edges — Ingest

| ID | Given / When / Then | Story |
|---|---|---|
| TC-ING-ME-01 | Given a Jira issue with `assignee: null`, `priority: null`, or `labels` absent entirely, When ingested, Then the connector does not raise and stores `None`/`[]` for the missing fields rather than crashing the whole batch. | SCRUM-7 |
| TC-ING-ME-02 | Given an `issuelinks` entry with neither `inwardIssue` nor `outwardIssue` (malformed), When ingested, Then that link is skipped and every other link is still normalized. | SCRUM-7 |
| TC-ING-ME-03 | Given GitHub returns 403/429 on `/pulls/{n}/reviews` for one PR but succeeds for others, When ingest runs, Then the failing PR's ingest failure is reported (not silently swallowed) and the other PRs still ingest successfully — a partial failure is visible, not masked as full success. | SCRUM-7 |
| TC-ING-ME-04 | Given Jira `/rest/api/3/search` returns 429, When ingest runs, Then the connector surfaces a retriable error (not a generic 500) and does not write partial/corrupt signal rows. | SCRUM-7 |
| TC-ING-ME-05 | Given the configured `story_points_field` id does not exist on the payload's `fields`, When ingested (mock/demo path), Then `meta.story_points` is `None`, not a `KeyError`. | SCRUM-7 |
| TC-ING-ME-06 | Given ingest is interrupted mid-run (process killed after 6 of 12 issues written), When ingest re-runs, Then all 12 persist with no duplicates for the 6 already written. | SCRUM-8 |

---

## DETECT — S3 Sprint health (SCRUM-9), S4 Hidden-risk detection (SCRUM-10)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-DET-01 | Given the ingested dataset, When the engine scores Sprint 3 at demo-now `2026-07-24`, Then overall status is `"green"` with a numeric score and named contributing factors. | SCRUM-9 (AC-DETECT) | PLANNED |
| TC-DET-02 | Given the score, Then it reports points completed vs. total (24/45 committed... exact per fixture), status breakdown 9 Done / 2 In Progress / 1 To Do, elapsed day 11/14, and burndown-vs-ideal variance. | SCRUM-9 | PLANNED |
| TC-DET-03 | Given a frontend request for sprint health, Then a single API response (`GET /projects/{id}/sprints/{sprint_id}/health`) includes the full burndown series (no second round-trip needed). | SCRUM-9 | PLANNED |
| TC-DET-04 | Given the same dataset, When scored twice (same injected `now`), Then the result is byte-for-byte deterministic. | SCRUM-9 | PLANNED |
| TC-DET-05 | Given SCRUM-42 is independently flagged `AT_RISK` (S4), Then the sprint health status is still `"green"` — health is NOT suppressed by the existing risk; both are simultaneously reportable from separate endpoints. **[E2E]** | SCRUM-9 | PLANNED |
| TC-DET-06 | Given the ingested dataset, When detection runs, Then exactly one story-level risk is raised: `SCRUM-42`, with severity, confidence, and a persisted `Risk` record. **[E2E]** | SCRUM-10 (AC-DETECT) | PLANNED |
| TC-DET-07 | Given SCRUM-42 (`In Progress`, `updated=2026-07-18`, 6d stale vs. demo-now) and PR #47 (open, non-draft, `base_ref="release/1.4"`, zero `APPROVED` reviews, 7d open), When evaluated, Then it is flagged `AT_RISK`. | SCRUM-10 | PLANNED |
| TC-DET-08 | Given the 9 Done stories, SCRUM-45 (In Progress but no release-branch PR blocking it), and SCRUM-51 (To Do), When evaluated, Then none is flagged — zero false positives. | SCRUM-10 | PLANNED |
| TC-DET-09 | Given SCRUM-42 flagged, Then the `Risk` record's `trigger_signal_ids` includes the exact `Signal.id`s for the stale-status issue, PR #47, and the correlated evidence — the set Explain (S5) will cite. | SCRUM-10 | PLANNED |
| TC-DET-10 | Given SCRUM-42 flagged, Then `reasons` names the release-gating context (`priority="Highest"`, `labels ⊇ {critical-path, release-1.4}`, `story_points=8`) and the "is blocked by SCRUM-45" link. | SCRUM-10 | PLANNED |
| TC-DET-11 | Given detection completes, Then the audit log contains one `DETECTION` record for the run. **[E2E]** | SCRUM-10 | PLANNED |
| TC-DET-12 | Given detection runs twice on unchanged data, Then no duplicate `Risk` rows are created (unique on `(project_id, risk_type, target_external_id)`, upsert semantics). | SCRUM-10 | PLANNED |

### Messy edges — Detect

| ID | Given / When / Then | Story |
|---|---|---|
| TC-DET-ME-01 | Given an issue is `In Progress` and stale (≥5d) but has **no** correlated release-branch PR at all, When evaluated, Then it does NOT flag (staleness alone is insufficient — both signals required). | SCRUM-10 |
| TC-DET-ME-02 | Given a PR is open, unapproved, and on `release/*`, but its correlated issue is `Done` or fresh (<5d stale), When evaluated, Then the issue does NOT flag. | SCRUM-10 |
| TC-DET-ME-03 | Given PR↔issue correlation relies on issue key in the PR title (SCRUM-42 in PR #47's title) — When the issue key is only present in `head_ref` (`feature/SCRUM-42`) and not the title, Then correlation still succeeds. | SCRUM-10 |
| TC-DET-ME-04 | Given the PR is in **draft** state (e.g. PR #44 for SCRUM-45) even though open on a non-release branch and unapproved, When evaluated, Then draft PRs are excluded from the "starved PR" signal (draft ≠ shipped work stalled). | SCRUM-10 |
| TC-DET-ME-05 | Given a stale issue whose only open PR is **approved**, When evaluated, Then it does NOT flag (an approved PR is not review-starved, even if not yet merged). | SCRUM-10 |
| TC-DET-ME-06 | Given `stale_days`/`pr_stale_days` thresholds are misconfigured to `0`, When evaluated against the curated dataset, Then QA's zero-false-positive assertion fails loudly in CI (a config regression is caught, not silently shipped). | SCRUM-10 |

---

## EXPLAIN — S5 Cited explanation (SCRUM-11)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-EXP-01 | Given SCRUM-42 is `AT_RISK`, When the explanation generates, Then it states the risk, its cause, and its consequence in plain business language (no field names/jargon). | SCRUM-11 (AC-EXPLAIN) | PLANNED |
| TC-EXP-02 | Given the explanation, Then citations include at minimum: SCRUM-42's `updated` date, PR #47 (open/unapproved/`base_ref=release/1.4`/age), the last SCRUM-42 commit date, the SCRUM-45 blocker, and one of {test T-1007 FAIL, incident INC-204}. **[E2E]** | SCRUM-11 | PLANNED |
| TC-EXP-03 | Given any citation in the explanation, When QA resolves `citation.signal_id`, Then it points to a real, stored `Signal` and `citation.quoted_value` matches that signal's field value **exactly** (character-for-character, not paraphrased). **[E2E]** | SCRUM-11 | PLANNED |
| TC-EXP-04 | Given the UI payload for an explanation, Then every citation carries a human-readable `label` and a `deep_link` to the source (Jira issue or GitHub PR/commit). | SCRUM-11 | PLANNED |
| TC-EXP-05 | Given unchanged underlying data, When the explanation is regenerated, Then the cited fact set (the set of `signal_id`s / `source_ref`s) is identical — prose may vary by LLM provider, but claims never exceed the citation set. | SCRUM-11 | PLANNED |
| TC-EXP-06 | Given a would-be citation whose underlying signal cannot be resolved (deleted/missing), When the explanation generates, Then that claim is **omitted entirely** — never rendered as an unsourced claim. | SCRUM-11 | PLANNED |
| TC-EXP-07 | Given `settings.llm_provider="anthropic"` and the provider is unavailable/errors, When explanation generation runs, Then it falls back to `TemplateProvider` and still produces a valid, fully-cited explanation (no 500, no silently missing explanation). | SCRUM-11 (messy edge) | PLANNED |
| TC-EXP-08 | Given the exact prompt payload sent to the LLM provider, Then it contains only already-ingested evidence fields (keys, dates, states, labels, actor names) — never secrets, tokens, full issue descriptions, or comment bodies. | SCRUM-11 (security) | PLANNED |

---

## ACT — S6 Governed action-bundle proposal (SCRUM-12)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-ACT-01 | Given SCRUM-42 is flagged and explained, When the agent proposes an action, Then it returns exactly one bundle with exactly 3 steps: escalate/request review on PR #47; comment on SCRUM-42 with cited evidence + at-risk flag; surface a SCRUM-45 re-prioritization recommendation. **[E2E]** | SCRUM-12 (AC-ACT) | PLANNED |
| TC-ACT-02 | Given each step in the bundle, Then it names the target system (`github`/`jira`), the operation, the target object, the payload, and a rationale linked to specific evidence signal IDs. | SCRUM-12 | PLANNED |
| TC-ACT-03 | Given a bundle is proposed, Then its status is `PENDING_APPROVAL` and the mock adapters have executed **zero** calls. **[E2E]** | SCRUM-12 | PLANNED |
| TC-ACT-04 | Given the mock adapters (`MockGitHubAdapter`/`MockJiraAdapter`), Then they never make a real network call to Jira/GitHub under any circumstance, and record every call they do receive (target, operation, payload, timestamp). | SCRUM-12 | PLANNED |
| TC-ACT-05 | Given a bundle is proposed, Then the proposal itself is audit-logged (`PROPOSED`, `actor="agent"`) before any approval step occurs. | SCRUM-12 | PLANNED |
| TC-ACT-06 | Given `settings.agent_enabled=false` (kill-switch off), When a proposal is requested, Then it is refused before any bundle is created — the kill-switch blocks proposal, not just execution. | SCRUM-12 (kill-switch) | PLANNED |
| TC-ACT-07 | Given a risk other than the SCRUM-42 demo risk type is passed to the proposer (out-of-scope input), When proposed, Then the proposer either declines cleanly or is explicitly scoped to reject — it must not silently fabricate an unrelated bundle. | SCRUM-12 (messy edge) | PLANNED |

---

## GOVERN — S7 Approval + immutable audit (SCRUM-13), S8 AuthN/RBAC (SCRUM-14)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-GOV-01 | Given a bundle is `PENDING_APPROVAL` and no approver acts, Then the mock adapters record **zero** calls, indefinitely (re-checked after a simulated delay, not just immediately after proposal). **[E2E]** | SCRUM-13 (AC-GOVERN) | PLANNED |
| TC-GOV-02 | Given an authorised `approver` approves the bundle, Then each of the 3 steps executes on the mock adapters and the bundle status becomes `EXECUTED`. **[E2E]** | SCRUM-13 | PLANNED |
| TC-GOV-03 | Given an approver rejects with a reason, Then no step executes, bundle status is `REJECTED`, and the reason is recorded in the audit entry. | SCRUM-13 | PLANNED |
| TC-GOV-04 | Given an approver edits one step then approves, Then only the approved/edited steps run, and **both** the original and edited versions are recorded in the audit trail. | SCRUM-13 | PLANNED |
| TC-GOV-05 | Given a step executes, Then its audit entry captures actor (`agent`), approver, timestamp, operation, target, evidence signal IDs, and the adapter's response — all non-null. **[E2E]** | SCRUM-13 | PLANNED |
| TC-GOV-06 | Given an attempted UPDATE or DELETE on an existing audit row (direct DB call, bypassing the app), Then it is rejected at the database layer (trigger/`REVOKE`), not merely by the app not exposing an update method. | SCRUM-13 | PLANNED |
| TC-GOV-07 | Given a completed demo loop, When QA queries the audit log, Then it holds at least one `DETECTION` record and at least one `EXECUTION` record — both stages traceable end-to-end. **[E2E]** | SCRUM-13 | PLANNED |
| TC-GOV-08 | Given a `viewer`-role token calls `POST /action-bundles/{id}/approve` **directly** (bypassing the UI), Then it is refused (403) and a `DENIED` audit entry is written. | SCRUM-13 + SCRUM-14 (RBAC) | PLANNED |
| TC-GOV-09 | Given valid credentials, When signing in, Then the returned session/token carries identity and role (`approver`/`viewer`). | SCRUM-14 (AC) | PLANNED |
| TC-GOV-10 | Given invalid credentials (wrong password, or unknown email), When signing in, Then access is denied with a generic message that does not reveal which factor (email vs. password) was wrong. | SCRUM-14 | PLANNED |
| TC-GOV-11 | Given an approver approves an action, Then their real identity is recorded in the audit entry — never a generic "system" or "agent" placeholder for the approver field. | SCRUM-14 | PLANNED |
| TC-GOV-12 | Given an unauthenticated caller, When hitting any protected endpoint (detection, explanation, action, audit, report), Then it is refused (401). | SCRUM-14 | PLANNED |
| TC-GOV-13 | Given a signed-in user, When the frontend reads `GET /auth/me`, Then identity and role are available to conditionally show/hide approval controls. | SCRUM-14 | PLANNED |
| TC-GOV-14 | Given a code review of the auth module, Then no hardcoded secrets exist and no password/token value appears in application logs. | SCRUM-14 | PLANNED |

### Messy edges — Govern

| ID | Given / When / Then | Story |
|---|---|---|
| TC-GOV-ME-01 | Given the kill-switch is flipped on mid-flight (bundle already `PENDING_APPROVAL`), When an approver then approves, Then execution is still blocked — the kill-switch is checked at execution time, not only at proposal time. | SCRUM-12/SCRUM-13 |
| TC-GOV-ME-02 | Given one of the 3 adapter calls fails during execution (simulated adapter error on step 2 of 3), Then the bundle is marked precisely per-step (not falsely `EXECUTED` in full), and the partial-execution state is audited accurately. | SCRUM-13 |
| TC-GOV-ME-03 | Given a `viewer` calls reject or edit (not just approve), Then both are refused identically to approve (403 + `DENIED`). | SCRUM-13/14 |
| TC-GOV-ME-04 | Given an approve request is submitted twice in quick succession (double-submit), Then execution happens exactly once (idempotent server-side handling), not twice. | SCRUM-13 |
| TC-GOV-ME-05 | Given a disabled user account attempts sign-in, Then authentication fails the same way as invalid credentials (no distinct signal that the account exists but is disabled). | SCRUM-14 |

---

## REPORT — S9 Executive summary (SCRUM-15)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-REP-01 | Given completed detection + explanation + an approved action, When the summary generates, Then it states: green surface, the SCRUM-42 risk with top evidence in one line, release impact, and the action taken + who approved it. **[E2E]** | SCRUM-15 (AC-REPORT) | PLANNED |
| TC-REP-02 | Given the summary is generated, Then zero manual authoring steps occurred (it is produced entirely from stored stage outputs). | SCRUM-15 | PLANNED |
| TC-REP-03 | Given a non-technical reader, Then the summary prose contains no field names or engineering jargon and uses human-readable issue/PR references (e.g. "SCRUM-42", "PR #47", not `external_id`/`meta.base_ref`). | SCRUM-15 | PLANNED |
| TC-REP-04 | Given the action bundle is still `PENDING_APPROVAL` when the summary is requested, Then the summary honestly reports the action as pending — it never claims an action was taken that wasn't. | SCRUM-15 | PLANNED |
| TC-REP-05 | Given the underlying data is demo-provenance, Then the summary is labelled "Demo data". | SCRUM-15 | PLANNED |
| TC-REP-06 | Given the summary is regenerated for the same `run_id`, Then the persisted content returned is identical (first generation is the source of truth; not recomputed/rephrased on every read). | SCRUM-15 | PLANNED |

---

## FRONTEND — S10 Dashboard + reveal (SCRUM-16), S11 Approval gate + audit UI (SCRUM-17)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-FE-01 | Given a signed-in user, When the dashboard loads Sprint 3, Then it shows green health, points, the 9/2/1 status breakdown, days remaining, and a burndown near ideal. | SCRUM-16 (AC) | PLANNED |
| TC-FE-02 | Given the green surface is displayed, When the risk reveal triggers, Then the contradiction is visible in **one view** — sprint still green AND SCRUM-42 at-risk shown together (progressive disclosure, not a state swap that hides green). | SCRUM-16 | PLANNED |
| TC-FE-03 | Given the revealed risk, Then a plain-language explanation renders with each cited fact as a distinct, labelled row linking to Jira/GitHub. | SCRUM-16 | PLANNED |
| TC-FE-04 | Given a displayed cited fact, Then its rendered value matches the stored `Signal` value exactly (no drift between API `quoted_value` and DOM text). | SCRUM-16 | PLANNED |
| TC-FE-05 | Given data with demo provenance, Then a persistent "Demo data" indicator remains visible across route changes (dashboard → risk detail → approval gate). | SCRUM-16 | PLANNED |
| TC-FE-06 | Given loading, error, and empty states, Then each renders a distinct, visible UI state — never a blank screen or a silent failure. | SCRUM-16 | PLANNED |
| TC-FE-07 | Given keyboard-only or screen-reader navigation, Then every control is reachable in a defined focus order, and risk status is conveyed by icon + text — never colour alone (WCAG 2.2 AA). | SCRUM-16 (a11y) | PLANNED |
| TC-FE-08 | Given a `PENDING_APPROVAL` bundle is opened, Then each of the 3 steps shows its target system, what will change, and evidence-linked rationale. | SCRUM-17 (AC) | PLANNED |
| TC-FE-09 | Given the bundle view, Then it is unmistakable (explicit banner/state) that nothing has executed yet and approval is required. | SCRUM-17 | PLANNED |
| TC-FE-10 | Given the approver clicks Approve, Then a confirmation step precedes execution, and per-step outcomes are shown after execution. | SCRUM-17 | PLANNED |
| TC-FE-11 | Given the approver clicks Reject, Then a reason is required before submit, and the UI confirms nothing executed. | SCRUM-17 | PLANNED |
| TC-FE-12 | Given the approver edits steps then approves, Then the UI states exactly which steps will run before the confirm action fires. | SCRUM-17 | PLANNED |
| TC-FE-13 | Given a `viewer`-role user, Then approval controls are visibly present but disabled, with an explanation shown (not silently hidden) — and the server still enforces 403 if bypassed (TC-GOV-08). | SCRUM-17 (RBAC, defense-in-depth) | PLANNED |
| TC-FE-14 | Given a completed run, When the audit view opens, Then detection + action records render chronologically with actor, approver, timestamp, operation, evidence, and adapter response. | SCRUM-17 | PLANNED |
| TC-FE-15 | Given the audit view, Then there is no edit affordance anywhere on the page (read-only by construction, not just by convention). | SCRUM-17 | PLANNED |
| TC-FE-16 | Given a double-click/double-submit on Approve, Then the button disables on submit and only one execution occurs (paired with TC-GOV-ME-04 on the server side). | SCRUM-17 (messy edge) | PLANNED |

*UX verification note:* per `docs/JIRA_WORKFLOW.md`, SCRUM-16 and SCRUM-17 additionally require UX sign-off on the built frontend PR before QA moves either to `stage-security`. QA does not substitute for UX review on these two stories — both are required.

---

## E2E — S12 One-command loop + 7 checkpoints (SCRUM-18)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-E2E-01 | Given a clean DB, When a single loop run is triggered for `SCRUM`, Then ingest → score → detect → explain → propose execute in order and the response includes a `run_id` and per-stage status. | SCRUM-18 (AC) | PLANNED |
| TC-E2E-02 | Given a completed run, Then all 7 checkpoints from `docs/qa/test-plan.md` §6 pass in a single automated assertion: green surface; SCRUM-42 flagged alone; cited explanation resolves; bundle `PENDING_APPROVAL` with zero calls; approval executes the 3 mock calls; audit holds detection + action; executive summary generated. This is the **headline test** for the whole platform. | SCRUM-18 | PLANNED |
| TC-E2E-03 | Given the loop reaches the approval gate with no approver acting, Then the run halts at `PENDING_APPROVAL` — it never auto-approves, under any configuration. | SCRUM-18 | PLANNED |
| TC-E2E-04 | Given a stage fails mid-run (e.g. detection throws), Then the failing stage is named in the run's stage-status list, and no downstream stage (explain/propose) is falsely marked successful. | SCRUM-18 | PLANNED |
| TC-E2E-05 | Given the loop is run twice on the same data, Then results are consistent and no duplicate signals or risks are created. | SCRUM-18 | PLANNED |
| TC-E2E-06 | Given the E2E test runs in CI, Then it requires no live Jira/GitHub network call (mock gateways + `TemplateProvider` only). | SCRUM-18 | PLANNED |
| TC-E2E-07 | Given the demo-critical rejection variant (per test-plan §6), When the approver rejects with reason instead of approving, Then the loop's audit trail shows `REJECTED` with zero execution, and the executive summary (if requested) reports "no action taken" honestly. | SCRUM-18 + SCRUM-13 + SCRUM-15 | PLANNED |

---

## PLATFORM — S13 Org data-source connections (SCRUM-19)

| ID | Given / When / Then | Story | Status |
|---|---|---|---|
| TC-CONN-01 | Given an admin, When they add a connection (source type, instance URL, credentials, target project/repo), Then it is saved and readable back (minus the credential). | SCRUM-19 (AC) | PLANNED |
| TC-CONN-02 | Given credentials are submitted, Then they are stored only via `SecretStore.put` (never a plaintext DB column), and are **never** returned on any subsequent read of the connection. | SCRUM-19 | PLANNED |
| TC-CONN-03 | Given a saved connection, When the admin clicks "Test connection", Then a real call is made to the source and success/failure is reported without echoing the credential or a sensitive error string. | SCRUM-19 | PLANNED |
| TC-CONN-04 | Given a working, enabled connection, When ingest runs for that org, Then it pulls from the configured connection — not any hardcoded `settings`-based source. | SCRUM-19 | PLANNED |
| TC-CONN-05 | Given two organizations each with their own connection and ingested signals, Then Org A cannot read Org B's connections or signals through any endpoint — including by guessing a numeric ID directly. | SCRUM-19 (tenant isolation) | PLANNED |
| TC-CONN-06 | Given an admin disables a connection, Then ingest immediately stops using it (next run does not pull from it) while the record and secret remain (soft-disable). | SCRUM-19 | PLANNED |
| TC-CONN-07 | Given an admin deletes a connection, Then the stored credential is purged from the `SecretStore` (verified by attempting `SecretStore.get(ref)` post-delete and confirming it's gone), not merely hidden in the UI. | SCRUM-19 | PLANNED |
| TC-CONN-08 | Given a non-admin (viewer/approver) attempts `POST /connections`, Then it is refused (403), consistent with S8's RBAC model. | SCRUM-19 | PLANNED |
| TC-CONN-09 | Given Postgres Row-Level Security is configured for `Connection` and `Signal`, When a direct SQL query is attempted under Org A's session context for Org B's rows, Then RLS denies the read at the database layer (DBA-owned; tested against real Postgres, not SQLite). | SCRUM-19 (tenant isolation, DB-level) | PLANNED |
| TC-CONN-10 | Given the same external Jira/GitHub `external_id` exists in both a demo dataset and a live-connected org, Then `provenance` + `org_id` scoping disambiguate them — no collision in the unique signal key. | SCRUM-19 (messy edge) | PLANNED |

---

## Summary — current pass state (as of this catalog's authoring)

| Stage | Cases written | PASS | FAIL | PLANNED |
|---|---|---|---|---|
| Ingest (S1/S2) | 16 + 6 messy-edge | 3 | 6 | 13 |
| Detect (S3/S4) | 12 + 6 messy-edge | 0 | 0 | 18 |
| Explain (S5) | 8 | 0 | 0 | 8 |
| Act (S6) | 7 | 0 | 0 | 7 |
| Govern (S7/S8) | 14 + 5 messy-edge | 0 | 0 | 19 |
| Report (S9) | 6 | 0 | 0 | 6 |
| Frontend (S10/S11) | 16 | 0 | 0 | 16 |
| E2E (S12) | 7 | 0 | 0 | 7 |
| Platform (S13) | 10 | 0 | 0 | 10 |

Ingest is the only stage with implementation to verify today (PR #1). Its FAIL entries are reported in detail on SCRUM-7 and SCRUM-8 as QA review comments with file/line evidence, input→expected→actual repro, and are not blocking Plan 1's own scope (workstream doc AC-INGEST) — only the tickets' fuller, since-finalized acceptance criteria. All other stages are `PLANNED`: this catalog exists so SCRUM-9…19 are built against known tests, not discovered after the fact.
