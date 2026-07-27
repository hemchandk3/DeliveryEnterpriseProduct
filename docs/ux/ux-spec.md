# UX Spec — Techwave Delivery Intelligence MVP (S9 / S10 / S11)

**Author:** UX Review (usability conscience)
**Date:** 2026-07-27
**Status:** Draft for architect fold-in (do **not** paste into Jira ticket descriptions directly — SCRUM-16/17 are being edited concurrently by the architect; this spec is folded in after).
**Related tickets:** SCRUM-15 (S9 Executive summary), SCRUM-16 (S10 Dashboard + reveal), SCRUM-17 (S11 Approval gate + governance/audit).
**Locked narrative:** `docs/mvp/2026-07-24-workstream-0-narrative-and-mocks.md`
**Engineering standards:** `docs/ENGINEERING_STANDARDS.md`

## Figma frames

File: `https://www.figma.com/design/i2tgva04xeQimcCxhRgyce`

| Screen | Frame | Direct link | Status |
|---|---|---|---|
| S10 · Delivery-health dashboard (green surface + hidden-risk reveal) | node `3:2` | `…?node-id=3-2` | Built + screenshot-verified |
| S10 · Evidence-cited explanation panel for SCRUM-42 | node `8:2` | `…?node-id=8-2` | Built + screenshot-verified |
| S11 · Agent approval gate (pending / approve / edit / reject) | node `11:2` | `…?node-id=11-2` | Built + screenshot-verified |
| S11 · Governance & audit view (permissions + decision trace + audit log) | node `14:2` | `…?node-id=14-2` | Built; **not yet screenshot-verified** (Figma Starter MCP call quota reached mid-session) |
| S9 · Executive summary | — | — | **Not built in Figma** (quota reached); fully specified below for direct build |

> Honesty note per the platform's own trust thesis: two artifacts are not visually confirmed this session. The dashboard, explanation panel, and approval gate were each screenshotted and corrected. The governance frame was assembled with the same verified helper code but not re-rendered; the executive summary exists only as this written spec. Both must be visually verified before UX sign-off (see §9).

---

## 1. How to read this spec

Every recommendation follows: **finding → violated/served principle → source → severity → concrete fix.** Sources are named (Nielsen heuristic number, a named Law of UX, Norman/Krug/Cooper/Shneiderman, or a WCAG 2.2 success criterion). Anything that is preference rather than evidence is explicitly labelled **[taste]**.

**Severity scale**
- **Blocker** — ships broken for a real persona/task, or fails a WCAG 2.2 AA criterion. Cannot pass UX verify.
- **High** — materially harms the core task (read risk → trust explanation → decide) but has a workaround.
- **Medium** — noticeable friction; fix within the sprint.
- **Low / Polish** — refinement.

Accessibility (WCAG 2.2 AA) is a **floor**, never traded for aesthetics (`docs/ENGINEERING_STANDARDS.md` §1 spirit; WCAG 2.2 AA). Contrast, keyboard, and focus are hard requirements.

---

## 2. Primary personas (per screen)

Usability is measured against a user and a task, never in the abstract (Cooper, *About Face* — design for the primary persona per screen).

| Screen | Primary persona | Their one job on this screen |
|---|---|---|
| S10 Dashboard | **Delivery manager under time pressure** | See at a glance whether the sprint is safe, and be shown the hidden risk the board hides — without hunting. |
| S10 Explanation | **PM who must trust before acting** | Verify *why* SCRUM-42 is at risk by inspecting the exact evidence, not a black-box score. |
| S11 Approval gate | **PM approver** | Understand exactly what the agent will do, to which system, on what evidence — then approve / edit / reject with confidence and accountability. |
| S11 Governance & audit | **PM approver + compliance/security reader** | Prove what happened: who could act, what was decided, and an immutable trace of both detection and action. |
| S9 Executive summary | **Executive / account manager** | Get status, the risk, and the action taken in ~20 seconds, in plain language, without a manual report. |

Secondary persona across all: **Viewer** (read-only). Their controls must be *disabled with explanation, never silently hidden* (Nielsen #1 visibility; Nielsen #10 help; and SCRUM-17 AC).

---

## 3. Cross-cutting design system & tokens

Color tokens live as Figma variables in collection `tokens` (23 variables). Semantics, not raw hex, are the contract:

- Surfaces: `bg/canvas` #EEF2F6, `bg/surface` #FFFFFF, `bg/subtle` #F8FAFC, `bg/sidebar` #0F172A.
- Text: `text/primary` #0F172A, `text/secondary` #475569, `text/muted` #64748B (**minimum** body-muted on white — see §8 contrast).
- Status (each ALWAYS paired with a text label or icon — never color alone): green `#15803D/#DCFCE7`, red `#B91C1C/#FEE2E2`, amber `#B45309/#FEF3C7`, info blue `#1D4ED8/#DBEAFE`.

**Type:** Inter. Ramp: 20 Bold (screen title) / 16 Bold (section) / 14–15 (body) / 12–13 (secondary) / 11 (labels). Body line-height ≥ 1.4× (supports WCAG 1.4.12 Text Spacing).

**Motion / responsiveness (Doherty Threshold, <400ms):** any state change — reveal, approve, execute — must acknowledge within 400ms with a skeleton or spinner, or it will feel broken and erode trust. Respect `prefers-reduced-motion` (WCAG 2.3.3 / 2.2 motion-sensitivity spirit): the reveal must have a non-animated equivalent.

**Universal state model (applies to every data surface).** Nielsen #1 (visibility of system status) requires each of these be *distinct and never a blank/silent fail* (SCRUM-16 AC "loading/error/empty → distinct states"):
1. **Loading** — skeleton of the real layout (not a bare spinner) so the eventual content is predictable.
2. **Empty** — explains *why* there's nothing and what to do next (Nielsen #10).
3. **Error** — plain-language cause + recovery action (Nielsen #9 help users recover; WCAG 3.3.1).
4. **Success / populated** — the designed state below.
5. **Stale/demo** — persistent "Demo data — curated, not live" indicator (narrative §Cold-start; honesty requirement).

---

## 4. S10 — Delivery-health dashboard + hidden-risk reveal (Frame `3:2`)

**Persona/task:** delivery manager, time-pressured — read safety, then be shown the hidden risk.

### 4.1 Layout
- **Dark left nav (240px)** — brand, primary sections, persona/role footer ("Delivery Manager · Approver"). Establishes *where I am* (Nielsen #1) and *who I am acting as* (needed for the govern story).
- **Top bar** — sprint identity (name, project, active, day 11/14, end date) + persistent **Demo-data** chip (top-right).
- **Green surface (above the fold):** health banner ("ON TRACK", health 92) → 4 metric cards (points burned, issues complete 9/12, days remaining, velocity) → story-point burndown (actual hugging ideal) + issue-status breakdown.
- **The reveal (progressive disclosure, same view):** a red attention banner — *"Delivery Intelligence found 1 hidden risk the board doesn't show"* — then the SCRUM-42 at-risk card (badge, one-line why, evidence chips, CTAs: **View cited evidence**, **Review recommended action**, Open in Jira).

### 4.2 The reveal pattern (the heart of the screen)
- **Progressive disclosure, not replacement.** The green surface must remain visible while the risk is revealed. Showing *both* truths at once is the insight (SCRUM-16 AC "contradiction visible in one view"). This directly serves **Nielsen #1** (honest status) and closes the **Gulf of Evaluation** (Norman) — the user perceives the true system state, not a flattering summary.
- **Von Restorff (isolation effect):** the single red risk card is deliberately the only saturated-red element on an otherwise calm green/neutral page, so the one thing that matters is the one thing that pops.
- **Zeigarnik effect:** the "1 hidden risk" open loop + the at-risk card's CTAs pull the user toward resolution (view evidence → act).
- **Gestalt common region + proximity:** the risk card groups badge + why + evidence + actions inside one bordered region so it reads as one object.

### 4.3 Findings (cited)

- **[Blocker] The reveal must be announced to assistive tech.** When the risk banner/card appears, screen-reader users get nothing. — WCAG **4.1.3 Status Messages**; Nielsen #1. **Fix:** render the reveal region with `role="status"`/`aria-live="polite"` (or move focus to it), so "1 hidden risk found: SCRUM-42 at risk" is announced.
- **[Blocker] Risk must not be conveyed by color alone.** Green/red carries the whole health message. — WCAG **1.4.1 Use of Color**; SCRUM-16 AC ("risk not conveyed by colour alone"). **Fix (already partly designed):** keep the text labels ("ON TRACK", "AT RISK"), the ▲ icon, and the word "Green"/"At risk"; ensure the burndown chart distinguishes Actual vs Ideal by **line style + label**, not just green vs grey (it currently uses solid vs dashed + a legend — retain that).
- **[High] Muted sub-labels fail contrast.** Metric-card sublabels and the risk card's "3 data-driven signals" use `#94A3B8` on white ≈ **2.6:1**. — WCAG **1.4.3 Contrast (Minimum)** (needs 4.5:1 for normal text). **Fix:** use `text/muted` `#64748B` (≈4.7:1) or darker for any text carrying meaning. Reserve #94A3B8 for on-dark surfaces only.
- **[High] Green banner subtitle contrast is borderline-failing.** `#15803D` on `#DCFCE7` ≈ **4.0:1**. — WCAG 1.4.3. **Fix:** darken subtitle text to `#166534` (matches the banner heading, ≈5.2:1) or lighten the banner background.
- **[Medium] Interactive citations need a ≥24px target.** "Open in Jira ↗" and evidence chips, if clickable, are ~15–24px tall text hit-areas. — WCAG **2.5.8 Target Size (Minimum)** (24×24). **Fix:** give links/chips ≥24px hit area (padding) and a visible focus ring (**2.4.7**).
- **[Medium] Metric internal consistency.** "Points burned" and the burndown must be driven by the same Detect output; the mock's point arithmetic is loose (narrative §4.2 sums don't reconcile). — Nielsen #2 (match the real world) / trust. **Fix:** bind all figures to the Detect engine's single source; never hand-type a headline number that can contradict a sibling number on the same card.
- **[Low/Polish] Keep the health score's meaning legible.** "92/100" is a composite; a novice may over-trust it. — Norman (conceptual model). **Fix [taste-adjacent, but sourced]:** on hover/focus, disclose the 2–3 factors behind the score (WCAG **1.4.13** content-on-focus rules apply to the tooltip).
- **[Serves] Miller's Law (7±2):** four metric cards + two panels keeps the surface within working-memory limits — do not add more headline metrics to this row.

### 4.4 Keyboard & focus
Logical focus order (WCAG **2.4.3**): skip-link → nav → top bar (demo chip is not focusable) → metric region → reveal banner → risk card (heading → evidence → CTAs). Sticky headers must not obscure the focused element (WCAG **2.4.11 Focus Not Obscured**).

---

## 5. S10 — Evidence-cited explanation panel, SCRUM-42 (Frame `8:2`)

**Persona/task:** PM who must trust before acting — verify *why*, fact by fact.

### 5.1 Layout
Right-side drawer (760px) over the dashboard: dark header (AT RISK badge, confidence, title, close ✕) → plain-language summary + a red one-line consequence ("will miss the release cutoff on 26 Jul") → **"Evidence — 5 cited signals"** header → five numbered evidence rows → footer ("Generated from ingested signals — no manual authoring", demo label, **Review recommended action →**).

### 5.2 The evidence row (the trust unit)
Each row = number badge · **category pill** (DETECTION / CRITICALITY / CAUSATION & STAKES) · bold claim · a **cited-value block** (source field path in muted mono-ish + the exact value in semibold) · "why it matters" · a source **link**.

- **Recognition over recall (Nielsen #6):** the reader never has to remember or reconstruct the data — the exact field and value are on-screen, each a distinct scannable row (SCRUM-16 UX-spec note).
- **Norman — closing the Gulf of Evaluation:** claim → evidence → source link lets the user verify the system's judgment against ground truth.
- **Krug — "Don't make me think":** the source path (`Jira · SCRUM-42 · fields.updated`) plus the resolved value ("2026-07-18 (6 days ago)") makes each fact self-evident and self-checking.
- **Category pill = Von Restorff + Nielsen #4 (consistency):** the three DETECTION rows read as the high-confidence core; CRITICALITY and CAUSATION are visibly a different class — matching the narrative's "core detection = signals 1,3,4" weighting.
- **Serial position effect:** strongest data-driven signal (stale status) is first; stakes/causation (blocker, Sev-2 incident) is last and memorable — the two ends carry the argument.

### 5.3 Findings (cited)

- **[Blocker] Every citation must resolve to a real, inspectable value.** SCRUM-16 AC ("displayed value matches stored signal"; "each cited fact resolves"). — Nielsen #2; trust thesis. **Fix:** each value is rendered from the ingested `Signal`, and the link opens the exact Jira issue / GitHub PR / commit / test / incident. No value may be templated or approximate.
- **[High] Panel must be a focus-trapped, escapable dialog.** As a drawer it needs keyboard containment and dismissal. — WCAG **2.1.2 No Keyboard Trap** (must be escapable), **2.4.3** focus order, Nielsen #3 (user control/freedom — clear exit). **Fix:** move focus to the panel heading on open; `Esc` and the ✕ (32×32, good per 2.5.8) close it; return focus to the triggering card.
- **[High] Category must not rely on color.** DETECTION-red / CAUSATION-amber must remain legible to color-blind users. — WCAG **1.4.1**. **Fix (already designed):** the pill carries the **word** ("DETECTION"), not just a hue — retain.
- **[Medium] Cited-value block contrast.** Source path is `#64748B` on `#F1F5F9` ≈ 4.3:1 — just under 4.5:1 for the 11px label. — WCAG 1.4.3. **Fix:** darken the source path to `#475569`, or lighten the block to #F8FAFC (≈4.7:1).
- **[Medium] Link ambiguity.** Five links read "Open … ↗"; a screen-reader "links list" would be repetitive. — WCAG **2.4.4 Link Purpose (In Context)** / **2.4.6**. **Fix:** ensure each link's accessible name is unique ("Open SCRUM-42 in Jira", "Open PR #47 in GitHub").
- **[Serves] Aesthetic-Usability Effect:** the calm, consistent row rhythm makes a dense evidence list feel trustworthy and easy — appropriate here because the *content* is the point; do not decorate further.

---

## 6. S11 — Agent approval gate: pending / approve / edit / reject (Frame `11:2`)

**Persona/task:** PM approver — understand exactly what will happen, then decide, with accountability.

### 6.1 Layout
Top bar (title, "executed only against mock systems after your approval", demo chip) → **PENDING banner** ("PENDING YOUR APPROVAL — nothing has executed yet", "0 of 3 steps run") → **action bundle** (3 step cards: target-system pill · operation · "What will change" · "Why" + evidence link · include toggle "Will run") → **decision bar** (Reject / Edit steps / **Approve & run 3 steps →**) → **"What each decision does"** strip (Pending / Approve / Edit / Reject outcomes).

### 6.2 State design (the four states)
- **Pending** — the default. It must be *unmistakable that nothing has run and approval is required* (SCRUM-17 AC). Served by: amber banner + "0 of 3 steps run" counter (Nielsen #1). This is a **Zeigarnik** open loop by design.
- **Approve** — **confirmation precedes execution** (a summary dialog listing the exact steps), then per-step outcomes are shown. — Nielsen #5 (error prevention) + Shneiderman rule 6 (easy reversal / here, *confirmation of the irreversible*) + Norman (forcing function on a consequential, hard-to-undo, people-visible action). The confirm step is mandatory because these actions change team-visible state (narrative §1.4 "why a human gate").
- **Edit** — the include toggles let the approver choose which steps run; the confirm screen then **states exactly which steps will run** (SCRUM-17 AC) — no surprise execution. — Nielsen #3 (user control) + #1 (visibility).
- **Reject** — **reason required**; UI confirms nothing executed; rejection + reason are audit-logged. — WCAG **3.3.1** (the required-reason field needs clear error identification if empty); Nielsen #9.

### 6.3 Findings (cited)

- **[Blocker] Confirmation dialog is mandatory and must be keyboard-operable.** The Approve button triggers real (mock) side-effects to people-visible systems. — Nielsen #5; Norman forcing function; WCAG **2.1.1** keyboard. **Fix:** interstitial confirm summary; default focus on a *non-destructive* control; `Esc` cancels; the primary "Confirm & run" is not the auto-focused default (prevents accidental Enter-to-execute).
- **[Blocker] Pending vs executed status must be a live status message.** State changes (0→3 run, per-step results) must reach assistive tech. — WCAG **4.1.3**. **Fix:** `aria-live="polite"` on the step-counter and per-step outcome region.
- **[High] Destructive/primary hierarchy via Fitts's Law.** "Approve & run" is the largest, highest-contrast, right-most target; "Reject" is present but visually quiet and separated. — **Fitts's Law** (size/position ∝ ease) + Nielsen #5. **Fix (already designed):** keep Approve as the largest target; keep Reject low-emphasis but **not** hidden. Do not place Reject immediately adjacent to Approve without a gap (avoids mis-click).
- **[High] Viewer role: disable, don't hide.** SCRUM-17 AC ("approval controls unavailable with explanation, not silently hidden"). — Nielsen #1 + #10; Norman (visible constraint). **Fix:** render Approve/Edit/Reject as disabled with an inline "You have Viewer access — ask an Approver" note; keep them perceivable (WCAG 1.4.3 disabled-state contrast is exempt but the *explanation* text must pass).
- **[Medium] The "Will run" toggle needs a real control semantic + target size.** — WCAG **2.5.8** (≥24×24; the 18px checkbox sits in a ~36px pill — OK) and **4.1.2 Name/Role/Value** (must expose checkbox state). **Fix:** implement as a labelled checkbox/switch with `aria-checked`; label reads "Step 1 — will run / excluded".
- **[Medium] Operation strings are jargon for the approver.** `add_comment + set_label( SCRUM-42 )` is developer-facing. — Nielsen #2 (match real world); Krug. **Fix:** lead with the plain "What will change" sentence (already present); keep the operation string as a secondary, monospace technical detail (`ENGINEERING_STANDARDS` §4 — plain language first).
- **[Serves] Tesler's Law (conservation of complexity):** the governance complexity is real and irreducible — the design *absorbs* it into an explicit gate rather than hiding it. That is correct for a governance product; do not "simplify" the gate away.

---

## 7. S11 — Governance & audit view (Frame `14:2`)

**Persona/task:** PM approver + compliance/security reader — prove what was permitted, decided, and done.

### 7.1 Layout
Top bar (title + persistent "🔒 Append-only · immutable" indicator) → **Permissions applied** (6 policy cards: approver identity/RBAC, agent execution scope = mock adapters only, human gate enforced, viewer read-only, evidence binding, audit integrity) → **Decision trace** (7-event chronological timeline: Ingest → Detect → Explain → Propose → Approve → Execute → Report, each with timestamp + actor + one-line detail) → **Audit log** (immutable table holding **both** the detection record and every action record; columns Time / Actor / Event / Detail-operation / Evidence signal IDs / Result) → footer ("append-only … both stages traceable end-to-end").

### 7.2 Why this satisfies the govern story
- **Both stages traceable** (SCRUM-17 AC + narrative §AC-GOVERN): the table's first row is `RISK_DETECTED` (detection record); rows 5–7 are the `EXECUTED` action records with mock adapter responses. The reader can prove detection *and* action.
- **No editing affordance** (SCRUM-17 AC): there is deliberately no edit/delete control; the "🔒 read-only" badge signals immutability (Norman — a *signifier* of the constraint; Nielsen #1).
- **Decision trace = closing the Gulf of Evaluation over time** (Norman): the approver can reconstruct the whole loop and attribute each step to an actor (agent vs human) — the accountability the human gate exists to create.
- **Gestalt similarity + Nielsen #4:** stage pills and result pills reuse the exact status semantics from S10/S11, so a red `AT_RISK` here means the same thing it meant on the dashboard (WCAG **3.2.4 Consistent Identification**).

### 7.3 Findings (cited)

- **[Blocker] The audit table must be a real semantic table.** Six-column data built from frames must expose row/column relationships. — WCAG **1.3.1 Info and Relationships** + **1.3.2 Meaningful Sequence**. **Fix:** implement as `<table>` with `<th scope>`; the Figma frame is the visual spec only.
- **[High] Evidence-ID cell density risks a horizontal scroll on narrow viewports.** — WCAG **1.4.10 Reflow** (no 2-D scroll at 320px-equiv). **Fix:** allow the "Evidence signal IDs" cell to wrap; the whole table gets its own `overflow-x:auto` region rather than forcing the page to scroll sideways.
- **[High] Result-pill status must not be color-only.** `AT_RISK` / `APPROVED` / `mock 200 OK`. — WCAG **1.4.1**. **Fix (already designed):** each pill carries the **word**; retain, and ensure pill text passes 1.4.3 (verify `#B45309` on `#FEF3C7` ≈4.8:1 ✓; `#15803D` on `#DCFCE7` ≈4.0:1 — **darken to `#166534`**).
- **[Medium] Timeline connector should be programmatic, not just visual.** Numbered badges imply order; assistive tech needs it too. — WCAG **1.3.1**. **Fix:** render the trace as an ordered list (`<ol>`); timestamps make sequence explicit in text.
- **[Medium] "🔒 immutable" is a claim the UI must not be able to violate.** — Nielsen #1 honesty; compliance. **Fix:** confirm with backend/dba that the store is truly append-only (row-level, no update/delete path) before the badge is shown; the badge must reflect reality, not decoration.
- **[Low] Emoji icons (🔒 👁) are inconsistent with a professional governance tool and may read differently across platforms.** — Nielsen #4 consistency; **[taste]** on the aesthetic, **sourced** on the accessibility: give each an `aria-hidden` + adjacent text label so meaning never depends on emoji rendering (WCAG 1.1.1). **Fix:** swap for the icon set used elsewhere; keep the text label.

### 7.4 Verification gap
This frame was assembled but **not screenshot-verified** this session (Figma quota). Before UX sign-off, re-render nodes `14:2` (permissions grid, decision trace, audit table) and check for: clipped wrapping text (the collapse bug seen and fixed on the dashboard), table column alignment, and the `#166534` contrast fix.

---

## 8. S9 — Executive summary (build-ready spec; Figma frame pending)

**Persona/task:** executive / account manager — status + risk + action in ~20 seconds, plain language, zero manual authoring (SCRUM-15).

### 8.1 Layout (single centered document column, ~860px)
1. **Header:** "Sprint 3 — Checkout Hardening · Executive summary", auto-generated timestamp, persistent **Demo-data** chip. Format like a document, not a dashboard — matches the reader's mental model of a status report (Jakob's Law — meet the convention they already know).
2. **One-line verdict (the peak):** a single sentence combining both truths — *"Sprint 3 is on track on the surface, but one release-critical story (Checkout payment retry) is at risk of missing the 26 Jul cutoff — and a corrective action has been taken."* This is the Serial-Position + **Peak-End** anchor: the first and most-remembered line.
3. **Status band:** green "On track (surface)" + red "1 release-critical risk" side by side — the same honest contradiction as S10, never one without the other (Nielsen #1; WCAG 1.4.1 — label both, not color alone).
4. **The risk, one line, plain language:** "Checkout payment retry hasn't moved in 6 days; its code change has waited a week for review, so release 1.4 is at risk." **No field names, no jargon, human-readable refs** ("Checkout payment retry", not "SCRUM-42.updated") — SCRUM-15 AC + `ENGINEERING_STANDARDS` §4.
5. **Action taken + who:** "Escalated the stalled review, flagged the story to the team, and surfaced the blocker — approved by Alex Rivera (Delivery Manager) at 09:12." If still pending, it must say **pending honestly** and not claim action was taken (SCRUM-15 AC).
6. **Footer:** "Generated automatically from delivery signals · Demo data" + a "View evidence" / "View audit trail" link into S10/S11 for anyone who wants to verify.

### 8.2 States (all required by SCRUM-15)
- **Approved-and-executed** (primary, above): states the action taken + approver.
- **Pending approval:** verdict changes to "…a corrective action is **proposed and awaiting approval**." — must **not** claim the action happened (Nielsen #1 honesty; SCRUM-15 AC). Visually: amber "Action pending" chip instead of green "Action taken".
- **No-risk (hypothetical):** "All stories on track; no action required." (Not in the demo path, but the component must render it without an empty red block.)
- **Regenerated for the same run:** content is **identical/persisted** (SCRUM-15 AC) — the summary is deterministic from the run, not re-authored. Nielsen #4 (consistency).
- Loading / error per the universal model (§3).

### 8.3 Findings / requirements (cited)

- **[Blocker] Plain language only — no field names in prose.** SCRUM-15 AC. — Nielsen #2; Krug; `ENGINEERING_STANDARDS` §4. **Fix:** a jargon lint in the generator; human-readable issue/PR titles, never keys, in the sentence body (keys may appear only in a small "references" line).
- **[Blocker] Pending must never read as done.** SCRUM-15 AC. — Nielsen #1. **Fix:** the "action" clause is generated from the *actual* action status, not assumed; unit-test both branches.
- **[High] Reading order & headings.** An exec skims with a screen reader too. — WCAG **1.3.1 / 2.4.6 Headings and Labels**. **Fix:** one `<h1>` (summary title), `<h2>` per band; the verdict is the first paragraph after `<h1>`.
- **[High] Contrast on the status band.** Reuse the darkened `#166534` green (§4/§7). — WCAG 1.4.3.
- **[Medium] Peak-End framing is deliberate, not decorative.** The one-line verdict is what the exec repeats to *their* stakeholders; it must be accurate and self-contained. — Peak-End Rule; Cooper (design for the primary persona's goal). **Fix:** the verdict sentence is generated to stand alone out of context (it will be copy-pasted).
- **[Serves] Hick's Law:** the exec screen offers *few* choices (read; optionally "view evidence"/"view audit"). Do not add filters, ranges, or controls here — decision-load belongs on S10/S11, not the summary.

---

## 9. Consolidated accessibility pass (WCAG 2.2 AA) — non-negotiable baseline

| Criterion | Where it bites | Requirement |
|---|---|---|
| 1.4.1 Use of Color | All status (green/red/amber) across S9–S11 | Always pair color with a text label + icon. |
| 1.4.3 Contrast (Min) | #94A3B8 sublabels; #15803D on #DCFCE7; #64748B on #F1F5F9 | Fix to ≥4.5:1 (normal text). Use #64748B min on white, #166534 on green bg, #475569 on #F1F5F9. |
| 1.4.11 Non-text Contrast | Chip/card borders, focus rings, chart lines | ≥3:1 for UI boundaries and the burndown lines vs background. |
| 1.3.1 Info & Relationships | Audit table, decision trace, evidence list | Real `<table>`/`<ol>` semantics; not frames. |
| 2.1.1 / 2.1.2 Keyboard | Explanation drawer, approval flow, confirm dialog | Fully operable; no trap; `Esc` closes overlays. |
| 2.4.3 Focus Order | Every screen | Logical order defined per screen (§4.4 pattern). |
| 2.4.7 Focus Visible | All interactive controls | Visible ≥3:1 focus indicator. |
| 2.4.11 Focus Not Obscured | Sticky top bars / drawer | Focused element never hidden behind sticky chrome. |
| 2.5.8 Target Size (Min) | Links, chips, toggles | ≥24×24 hit area. |
| 3.2.4 Consistent Identification | Status semantics reused S10→S11→S9 | Same meaning, same treatment everywhere. |
| 3.3.1 Error Identification | Reject-reason field; confirm dialogs | Clear, text error messages. |
| 4.1.2 Name/Role/Value | "Will run" toggles, buttons | Correct roles/states exposed. |
| 4.1.3 Status Messages | Risk reveal; approve/execute outcomes; pending counter | `aria-live` announcements. |

Accessibility is a floor, not a trade — no aesthetic change may regress any row above (`ENGINEERING_STANDARDS` spirit; WCAG 2.2 AA).

## 10. Consolidated Nielsen heuristic pass

1. **Visibility of system status** — health banner, demo chip, pending counter, per-step outcomes, immutable badge. ✔ (add the aria-live's above).
2. **Match real world** — plain language first; jargon demoted to secondary (S9, S11 operation strings).
3. **User control & freedom** — drawer `Esc`/✕; confirm dialog cancel; edit-which-steps; reject.
4. **Consistency & standards** — one status vocabulary S9→S11; Jakob's Law on S9 (report convention).
5. **Error prevention** — mandatory confirm before irreversible/mock execution; reject-reason required.
6. **Recognition over recall** — evidence rows show source + value inline; nothing to remember.
7. **Flexibility/efficiency** — keyboard paths; "view evidence/audit" shortcuts from S9. (MVP scope: no power-user customization — correct per tickets' out-of-scope.)
8. **Aesthetic & minimalist** — calm surface; the *one* red risk isolated (Von Restorff). Density is intentional for an expert tool — do not strip signal for prettiness.
9. **Help users recover** — plain-language errors; reject/edit reversibility before commit.
10. **Help & documentation** — viewer-role explanation; score/tooltip disclosure; "why it matters" per evidence row.

## 11. Verify & Validate protocol (for UX sign-off)

**Verify (heuristic + WCAG checklist):** run each frame through §9 and §10; confirm every finding above maps to a named source; confirm the four contrast fixes (#94A3B8, #166534 ×2, source-path) are applied.

**Validate (task walkthrough for the primary persona):** the delivery manager/PM must be able to **read risk → understand the cited explanation → approve/deny the agent action** with minimal cognitive load. Walk the Gulf of Execution (can they find how to act? — CTAs "View evidence"/"Review action"/"Approve") and the Gulf of Evaluation (can they tell what happened? — status banners, per-step outcomes, audit trace).

**Re-review after developer applies fixes:** confirm the cited violation is actually *resolved*, not moved. Per SCRUM-16/17 workflow: after the frontend PR lands and while the ticket is Ready for QA / In Review, UX verifies against this spec. **Pass →** allow QA to move to Ready for Security. **Fail →** move to In Progress + Developer with the specific unmet clause. No UI story reaches Ready for Security without the UX verify comment.

## 12. Severity-ranked open items (do first)

1. **[Blocker]** aria-live on: risk reveal (S10), approve/execute outcomes + pending counter (S11) — WCAG 4.1.3.
2. **[Blocker]** Mandatory, keyboard-operable confirm dialog before Approve executes — Nielsen #5 / Norman.
3. **[Blocker]** Real semantic table for the audit log; ordered list for the trace — WCAG 1.3.1.
4. **[Blocker]** Plain-language / pending-honesty guarantees in S9 generator — SCRUM-15 AC.
5. **[High]** Four contrast fixes (§9) — WCAG 1.4.3.
6. **[High]** Viewer role: disabled-with-explanation controls — SCRUM-17 AC.
7. **[High]** Table reflow / evidence-cell wrapping — WCAG 1.4.10.
8. **[Medium]** ≥24px targets on links/chips/toggles — WCAG 2.5.8; correct roles — 4.1.2.
9. **[Medium]** Verify the un-screenshotted governance frame + build the S9 frame in Figma once quota resets.
