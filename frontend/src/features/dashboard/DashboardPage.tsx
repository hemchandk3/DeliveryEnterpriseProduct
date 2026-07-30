import { useSprintHealth, useRiskReveal } from "@/api/queries";
import { StateBoundary } from "@/components/StateBoundary";
import { Skeleton } from "@/components/ui/skeleton";
import { BurndownChart } from "./BurndownChart";
import { RiskReveal } from "./RiskReveal";
import { SprintHealthPanel } from "./SprintHealthPanel";

interface DashboardPageProps {
  /** Sourced from the selected `Project` (`GET /projects`) -- never hardcoded. */
  projectId: number;
  /** The project's current sprint, from `Project.latest_health.sprint_external_id`. */
  sprintId: string;
}

/**
 * The delivery-health dashboard (SCRUM-16): the green surface and the
 * hidden-risk reveal in one view, for whichever project the top-bar
 * `ProjectSelector` (in `App.tsx`) currently has selected. Data flow per
 * ARCHITECTURE.md §5.6: `GET /projects/{id}/sprints/{sprint_id}/health` for
 * the surface, `GET /projects/{id}/risks` (+ an auto-triggered
 * `POST .../risks/detect` the first time it's empty — see
 * `api/queries.ts::useRiskReveal`) for the reveal.
 */
export function DashboardPage({ projectId, sprintId }: DashboardPageProps) {
  const healthQuery = useSprintHealth(projectId, sprintId);
  const risksQuery = useRiskReveal(projectId);
  const health = healthQuery.data;

  return (
    <main id="main-content" tabIndex={-1} className="flex flex-1 flex-col gap-8 px-6 py-6 focus:outline-none">
      <div>
        <h1 className="text-xl font-bold text-text-primary">
          {health?.name ?? "Sprint health"}
        </h1>
        {health && (
          <p className="text-sm text-text-secondary">
            Day {health.elapsed_days} of {health.total_days}
          </p>
        )}
      </div>

      <StateBoundary
        state={{
          isLoading: healthQuery.isLoading,
          isError: healthQuery.isError,
          error: healthQuery.error,
          refetch: () => void healthQuery.refetch(),
        }}
        loadingFallback={
          <div className="flex flex-col gap-4">
            <Skeleton className="h-16 w-full" />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {["a", "b", "c", "d"].map((placeholderKey) => (
                <Skeleton key={placeholderKey} className="h-24 w-full" />
              ))}
            </div>
            <Skeleton className="h-56 w-full" />
          </div>
        }
      >
        {health && (
          <>
            <SprintHealthPanel health={health} />
            <BurndownChart burndown={health.burndown} />
          </>
        )}
      </StateBoundary>

      <RiskReveal risksQuery={risksQuery} />
    </main>
  );
}
