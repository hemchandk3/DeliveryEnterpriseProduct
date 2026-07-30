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
