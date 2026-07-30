/**
 * Typed mirror of the backend's Detect-stage response contracts.
 *
 * Source of truth: `backend/app/risk/schemas.py` (SCRUM-9, SCRUM-10) and
 * `docs/ARCHITECTURE.md` §5.2/§5.6. Keep these in lockstep with the Pydantic
 * models by hand -- there is no shared codegen yet (a fair follow-up once
 * the backend OpenAPI schema stabilizes across more stories).
 *
 * Field names are copied verbatim (snake_case) rather than transformed to
 * camelCase, so a value on screen can always be traced back to the exact
 * JSON key the backend returned -- this matters for the "displayed value
 * matches stored signal" acceptance criterion (SCRUM-16 AC).
 */

export interface BurndownPoint {
  date: string; // ISO date (YYYY-MM-DD)
  ideal_remaining: number;
  actual_remaining: number;
}

export interface HealthFactor {
  name: string;
  value: number;
  weight: number;
  contribution: number;
}

export type SprintHealthStatus = "green" | "amber" | "red";

export interface SprintHealth {
  sprint_external_id: string;
  name: string | null;
  status: SprintHealthStatus;
  score: number;
  points_total: number;
  points_done: number;
  points_in_progress: number;
  points_todo: number;
  issues_done: number;
  issues_in_progress: number;
  issues_todo: number;
  elapsed_days: number;
  total_days: number;
  burndown: BurndownPoint[];
  factors: HealthFactor[];
}

/**
 * Per-project latest computed sprint health, as embedded on `Project` by
 * `GET /projects` (ARCHITECTURE.md §5.7 `ProjectHealthSnapshot`, exposed via
 * §5.6 `GET /projects`). This is what lets the UI go straight from "which
 * project" to "which sprint" without a separate sprint picker -- there is
 * exactly one current snapshot per project in the MVP loop-runner model.
 */
export interface ProjectHealthSummary {
  sprint_external_id: string;
  status: SprintHealthStatus;
  score: number;
  computed_at: string;
}

/**
 * `GET /projects` row (ARCHITECTURE.md §5.6/§13.7, tech doc
 * multi-tenancy-and-project-grain.html §4). Tenant scoping is enforced
 * server-side from the JWT's `org_id` -- every id on this type is already
 * scoped to the caller's tenant; the frontend never accepts or sends an
 * org id itself (ADR-006).
 */
export interface Project {
  id: number;
  key: string;
  name: string;
  latest_health: ProjectHealthSummary | null;
}

export interface ProjectListResponse {
  items: Project[];
  next_cursor: string | null;
}

// TODO(SCRUM-19): connections management (list/edit/test/delete existing
// connections) is its own ticket and its own UI, out of SCRUM-16 scope.
// These two types + the create-project/create-connection calls in
// client.ts exist so the dashboard's "Connect a project" entry point is a
// real, typed call against the documented contract (ARCHITECTURE.md §5.6
// `POST /projects`, `POST /projects/{id}/connections`) rather than a dead
// button -- see ConnectProjectDialog.tsx.
export type ConnectionSourceType = "jira" | "github" | "demo";

export interface Connection {
  id: number;
  project_id: number;
  source_type: ConnectionSourceType;
  display_name: string;
  enabled: boolean;
}

export interface EvidenceRef {
  signal_id: number;
  kind: string;
  label: string;
}

export interface RiskFinding {
  risk_type: string;
  target_external_id: string;
  severity: string;
  confidence: number;
  status: "AT_RISK";
  reasons: string[];
  trigger_signal_ids: number[];
  evidence_refs: EvidenceRef[];
}

// TODO(SCRUM-11): once `GET /risks/{risk_id}/explanation` lands, add
// `Explanation` / `Citation` types here (per ARCHITECTURE.md §5.3:
// Citation{kind,label,source_ref,field,quoted_value,deep_link,signal_id},
// Explanation{risk_id,summary,cause,consequence,citations[],provenance,model})
// and swap ExplanationPanel/CitationRow over from RiskFinding.reasons /
// evidence_refs to the real cited fields (source_ref, quoted_value,
// deep_link). See src/features/dashboard/ExplanationPanel.tsx.

/** Shape of a FastAPI/Starlette default error body, e.g. `{"detail": "..."}`. */
export interface ApiErrorBody {
  detail?: string;
}
