import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import {
  createConnection,
  createProject,
  detectRisks,
  getProjects,
  getRisks,
  getSprintHealth,
} from "./client";
import type {
  Connection,
  ConnectionSourceType,
  Project,
  ProjectListResponse,
  RiskFinding,
  SprintHealth,
} from "./types";

export const queryKeys = {
  projects: () => ["projects"] as const,
  sprintHealth: (projectId: number, sprintId: string) =>
    ["sprint-health", projectId, sprintId] as const,
  risks: (projectId: number) => ["risks", projectId] as const,
};

/**
 * `GET /projects` -- the tenant's real, actually-connected project list.
 * Drives `ProjectSelector` and the first-run "no projects connected" empty
 * state. Never backed by a hardcoded/demo project (coordinator scope-change
 * requirement: no demo data in the UI).
 */
export function useProjects(): UseQueryResult<ProjectListResponse> {
  return useQuery({
    queryKey: queryKeys.projects(),
    queryFn: () => getProjects(),
  });
}

/**
 * TODO(SCRUM-19): the full connections management flow (list/test/edit/
 * delete) belongs to its own ticket/UI. These two mutations back the
 * minimal "Connect a project" entry point (ConnectProjectDialog.tsx) --
 * real, typed calls against the documented contract; today they are
 * expected to fail honestly (404/501) until SCRUM-19 ships the backend.
 */
export function useCreateProject(): UseMutationResult<
  Project,
  unknown,
  { key: string; name: string }
> {
  const queryClient = useQueryClient();
  return useMutation({
    // Wrapped (not passed by reference): react-query's mutation executor
    // invokes `mutationFn` with an internal second argument, and a
    // reference like `mutationFn: createProject` would silently forward
    // that extra arg straight into the fetch client. Wrapping pins the
    // call to exactly the one documented parameter.
    mutationFn: (input: { key: string; name: string }) => createProject(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects() });
    },
  });
}

export function useCreateConnection(): UseMutationResult<
  Connection,
  unknown,
  {
    projectId: number;
    source_type: ConnectionSourceType;
    display_name: string;
    base_url: string;
    project_ref: string;
  }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, ...input }) => createConnection(projectId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects() });
    },
  });
}

export function useSprintHealth(
  projectId: number,
  sprintId: string
): UseQueryResult<SprintHealth> {
  return useQuery({
    queryKey: queryKeys.sprintHealth(projectId, sprintId),
    queryFn: () => getSprintHealth(projectId, sprintId),
  });
}

/**
 * Reads `GET /projects/{id}/risks` and, the first time it comes back empty,
 * fires `POST /projects/{id}/risks/detect` once and refetches.
 *
 * Why: SCRUM-18 (the loop runner that would normally sequence
 * Ingest -> Detect -> ... end to end) isn't built yet, so nothing else in
 * the system currently triggers detection. This hook still only ever calls
 * the backend's real endpoints and renders whatever they return -- it does
 * not score, filter, or otherwise decide what counts as a risk; it just
 * makes sure the (already-designed) detect step has run once so the reveal
 * has real data. See `docs/ARCHITECTURE.md` §5.6 and `api/client.ts`.
 */
export function useRiskReveal(projectId: number): UseQueryResult<RiskFinding[]> {
  const queryClient = useQueryClient();
  const hasTriggeredDetect = useRef(false);

  const query = useQuery({
    queryKey: queryKeys.risks(projectId),
    queryFn: () => getRisks(projectId),
  });

  useEffect(() => {
    if (
      query.isSuccess &&
      query.data.length === 0 &&
      !hasTriggeredDetect.current
    ) {
      hasTriggeredDetect.current = true;
      void detectRisks(projectId).then(() => {
        void queryClient.invalidateQueries({ queryKey: queryKeys.risks(projectId) });
      });
    }
  }, [query.isSuccess, query.data, projectId, queryClient]);

  return query;
}
