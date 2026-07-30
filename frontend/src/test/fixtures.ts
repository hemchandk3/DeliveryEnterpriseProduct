import type { Project, ProjectListResponse, RiskFinding, SprintHealth } from "@/api/types";

export function makeSprintHealth(overrides: Partial<SprintHealth> = {}): SprintHealth {
  return {
    sprint_external_id: "3",
    name: "Sprint 3 — Checkout Hardening",
    status: "green",
    score: 92,
    points_total: 40,
    points_done: 28,
    points_in_progress: 8,
    points_todo: 4,
    issues_done: 9,
    issues_in_progress: 2,
    issues_todo: 1,
    elapsed_days: 11,
    total_days: 14,
    burndown: [
      { date: "2026-07-15", ideal_remaining: 40, actual_remaining: 40 },
      { date: "2026-07-18", ideal_remaining: 28, actual_remaining: 30 },
      { date: "2026-07-22", ideal_remaining: 14, actual_remaining: 12 },
    ],
    factors: [
      { name: "velocity", value: 0.9, weight: 0.4, contribution: 36 },
      { name: "scope_stability", value: 0.95, weight: 0.3, contribution: 28.5 },
      { name: "blocker_rate", value: 0.9, weight: 0.3, contribution: 27.5 },
    ],
    ...overrides,
  };
}

export function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 1,
    key: "SCRUM",
    name: "Checkout Hardening",
    latest_health: {
      sprint_external_id: "3",
      status: "green",
      score: 92,
      computed_at: "2026-07-28T09:00:00Z",
    },
    ...overrides,
  };
}

export function makeProjectListResponse(
  overrides: Partial<ProjectListResponse> = {}
): ProjectListResponse {
  return {
    items: [makeProject()],
    next_cursor: null,
    ...overrides,
  };
}

export function makeRiskFinding(overrides: Partial<RiskFinding> = {}): RiskFinding {
  return {
    risk_type: "stalled_release_critical",
    target_external_id: "SCRUM-42",
    severity: "high",
    confidence: 0.87,
    status: "AT_RISK",
    reasons: [
      "SCRUM-42 has not moved status in 6 days.",
      "Its linked PR has waited 7 days for review.",
      "A Sev-2 incident references this story as the likely cause.",
    ],
    trigger_signal_ids: [101, 102, 103],
    evidence_refs: [
      { signal_id: 101, kind: "jira/issue", label: "SCRUM-42 · fields.updated" },
      { signal_id: 102, kind: "github/pr", label: "PR #47 · review pending" },
      { signal_id: 103, kind: "github/commit", label: "Commit a1b2c3" },
    ],
    ...overrides,
  };
}
