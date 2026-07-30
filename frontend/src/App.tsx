import { useEffect, useMemo, useState } from "react";
import { useProjects } from "@/api/queries";
import { StateBoundary } from "@/components/StateBoundary";
import { Skeleton } from "@/components/ui/skeleton";
import { AppShell } from "./layout/AppShell";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { ProjectSelector } from "./features/projects/ProjectSelector";
import { ConnectProjectDialog } from "./features/projects/ConnectProjectDialog";
import { NoProjectsEmptyState } from "./features/projects/NoProjectsEmptyState";

/**
 * Top-level orchestration: which tenant project is selected, and what to
 * render for it. Replaces the earlier `VITE_PROJECT_ID`/`VITE_SPRINT_ID`
 * env-configured single project (coordinator scope-change: no hardcoded or
 * demo project in the UI). The project list comes from the real
 * `GET /projects` call (`useProjects`, tenant-scoped server-side from the
 * JWT per ADR-006) -- every id the dashboard uses downstream is sourced
 * from that response, never typed in or defaulted client-side.
 */
export default function App() {
  const projectsQuery = useProjects();
  const projects = useMemo(() => projectsQuery.data?.items ?? [], [projectsQuery.data]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  useEffect(() => {
    if (selectedProjectId === null && projects.length > 0) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null;
  const showEmptyState = projectsQuery.isSuccess && projects.length === 0;

  return (
    <AppShell
      topBar={
        <>
          <ProjectSelector
            projectsQuery={projectsQuery}
            selectedProjectId={selectedProjectId}
            onSelect={setSelectedProjectId}
          />
          {!showEmptyState && (
            <div className="ml-auto">
              <ConnectProjectDialog />
            </div>
          )}
        </>
      }
    >
      {showEmptyState ? (
        <NoProjectsEmptyState />
      ) : (
        <StateBoundary
          state={{
            isLoading: projectsQuery.isLoading,
            isError: projectsQuery.isError,
            error: projectsQuery.error,
            refetch: () => void projectsQuery.refetch(),
          }}
          loadingFallback={
            <div className="flex flex-col gap-4 px-6 py-6">
              <Skeleton className="h-16 w-full" />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {["a", "b", "c", "d"].map((placeholderKey) => (
                  <Skeleton key={placeholderKey} className="h-24 w-full" />
                ))}
              </div>
            </div>
          }
        >
          {selectedProject?.latest_health ? (
            <DashboardPage
              projectId={selectedProject.id}
              sprintId={selectedProject.latest_health.sprint_external_id}
            />
          ) : selectedProject ? (
            <div className="m-6 flex flex-col items-start gap-1 rounded-lg border border-border bg-subtle p-4 text-text-secondary">
              <p className="font-semibold text-text-primary">No sprint health computed yet</p>
              <p className="text-sm">
                {selectedProject.name} is connected, but Delivery Intelligence hasn't computed a
                sprint health snapshot for it yet.
              </p>
            </div>
          ) : null}
        </StateBoundary>
      )}
    </AppShell>
  );
}
