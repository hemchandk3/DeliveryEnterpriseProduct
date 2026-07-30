import { useQuery, useQueryClient, type UseQueryResult } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { detectRisks, getRisks, getSprintHealth } from "./client";
import type { RiskFinding, SprintHealth } from "./types";

export const queryKeys = {
  sprintHealth: (projectId: number, sprintId: string) =>
    ["sprint-health", projectId, sprintId] as const,
  risks: (projectId: number) => ["risks", projectId] as const,
};

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
