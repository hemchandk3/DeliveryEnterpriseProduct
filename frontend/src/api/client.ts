import type {
  ApiErrorBody,
  Connection,
  ConnectionSourceType,
  Project,
  ProjectListResponse,
  RiskFinding,
  SprintHealth,
} from "./types";

/**
 * Typed API client for the Detect-stage backend surface (ARCHITECTURE.md
 * §5.6). Every call goes to the real FastAPI backend -- in dev via the Vite
 * proxy configured in `vite.config.ts` (`/api/*` -> `http://localhost:8000`
 * by default), in production via whatever same-origin/reverse-proxy path
 * ops wires up. There is no mock/stub path in this module: per
 * `docs/ENGINEERING_STANDARDS.md` §1, the frontend renders the backend's
 * truth, it does not invent it.
 */

const API_BASE = "/api";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string | undefined;

  constructor(status: number, detail: string | undefined, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// TODO(SCRUM-14 / S8 auth): this platform is auth-gated per the SCRUM-16
// technical design ("Auth-gated (S8): an unauthenticated load redirects to
// sign-in"), but `POST /auth/login` / `GET /auth/me` are not built yet. Wire
// a bearer token here (e.g. read from an auth context/localStorage) once
// that lands; today every request is unauthenticated, matching the current
// backend, which does not yet enforce a session.
function authHeaders(): HeadersInit {
  return {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...authHeaders(),
        ...init?.headers,
      },
    });
  } catch (cause) {
    // Network failure (backend unreachable, dev proxy down, offline, etc.)
    // -- distinct from an HTTP error status so callers/UI can tell "the
    // server said no" apart from "we couldn't reach the server".
    throw new ApiError(0, undefined, "Network error: could not reach the delivery-intelligence API");
  }

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const body = (await response.json()) as ApiErrorBody;
      detail = body.detail;
    } catch {
      // Response wasn't JSON (or was empty) -- fall back to status text.
    }
    throw new ApiError(
      response.status,
      detail,
      detail || `Request failed with status ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/**
 * `GET /projects` -- ARCHITECTURE.md §5.6, cursor-paginated (§13.7). This is
 * the tenant's actually-connected project list (never a hardcoded/demo
 * one) and is what feeds `ProjectSelector`. Tenant scoping happens
 * server-side from the JWT; no org id is ever passed here.
 */
export function getProjects(cursor?: string): Promise<ProjectListResponse> {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
  return request<ProjectListResponse>(`/projects${query}`);
}

// TODO(SCRUM-19 / SCRUM-connections): `POST /projects` and
// `POST /projects/{id}/connections` are designed (ARCHITECTURE.md §5.6) but
// not yet implemented by the backend -- SCRUM-19 (connections) is still
// `stage-todo`. These calls are wired for real so the "Connect a project"
// entry point (ConnectProjectDialog.tsx) is honest: it will surface the
// backend's real 404/501 today via ApiError, never fake a created project.
export function createProject(input: { key: string; name: string }): Promise<Project> {
  return request<Project>(`/projects`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function createConnection(
  projectId: number,
  input: {
    source_type: ConnectionSourceType;
    display_name: string;
    base_url: string;
    project_ref: string;
  }
): Promise<Connection> {
  return request<Connection>(`/projects/${projectId}/connections`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

/** `GET /projects/{id}/sprints/{sprint_id}/health` -- ARCHITECTURE.md §5.6. */
export function getSprintHealth(projectId: number, sprintId: string): Promise<SprintHealth> {
  return request<SprintHealth>(`/projects/${projectId}/sprints/${sprintId}/health`);
}

/** `GET /projects/{id}/risks` -- ARCHITECTURE.md §5.6. */
export function getRisks(projectId: number): Promise<RiskFinding[]> {
  return request<RiskFinding[]>(`/projects/${projectId}/risks`);
}

/**
 * `POST /projects/{id}/risks/detect` -- ARCHITECTURE.md §5.6.
 *
 * This re-runs (idempotently -- persistence upserts on
 * `(project_id, risk_type, target_external_id)`) the Detect stage's risk
 * scan and persists the result. Until the loop runner (SCRUM-18) exists to
 * orchestrate Ingest -> Detect end-to-end, the dashboard calls this itself
 * the first time `GET /risks` comes back empty (see
 * `src/features/dashboard/useRiskReveal.ts`) so the reveal has something
 * real to show. This does not compute or decide anything client-side --
 * it only asks the backend's own detector to run.
 */
export function detectRisks(projectId: number): Promise<RiskFinding[]> {
  return request<RiskFinding[]>(`/projects/${projectId}/risks/detect`, { method: "POST" });
}
