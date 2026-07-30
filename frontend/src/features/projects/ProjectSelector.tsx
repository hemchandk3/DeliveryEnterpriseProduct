import type { UseQueryResult } from "@tanstack/react-query";
import { ChevronDown } from "lucide-react";
import type { ProjectListResponse } from "@/api/types";
import { Skeleton } from "@/components/ui/skeleton";

interface ProjectSelectorProps {
  projectsQuery: UseQueryResult<ProjectListResponse>;
  selectedProjectId: number | null;
  onSelect: (projectId: number) => void;
}

/**
 * The tenant's real, actually-connected project list (`GET /projects`) --
 * never a hardcoded or demo project (coordinator scope-change requirement).
 * A native `<select>` on purpose: full keyboard/screen-reader support for
 * free, no new dependency, no bespoke combobox to get wrong (WCAG 4.1.2,
 * 2.1.1). Rendered in the app's top bar so "which project am I looking at"
 * is always visible (Nielsen #1) and switching never leaves the dashboard.
 */
export function ProjectSelector({ projectsQuery, selectedProjectId, onSelect }: ProjectSelectorProps) {
  if (projectsQuery.isLoading) {
    return <Skeleton className="h-9 w-48" />;
  }

  if (projectsQuery.isError) {
    // The top bar has limited room for a full StateBoundary error card;
    // this is still a distinct, honest state (never silent), and the
    // full-page StateBoundary below the top bar carries the retry action.
    return <span className="text-sm text-status-red">Couldn't load projects</span>;
  }

  const projects = projectsQuery.data?.items ?? [];
  if (projects.length === 0) {
    return null;
  }

  return (
    <div className="relative">
      <label htmlFor="project-selector" className="sr-only">
        Project
      </label>
      <select
        id="project-selector"
        className="min-h-[36px] appearance-none rounded-md border border-border bg-surface py-1.5 pl-3 pr-9 text-sm font-medium text-text-primary hover:bg-subtle"
        value={selectedProjectId ?? ""}
        onChange={(event) => onSelect(Number(event.target.value))}
      >
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name} ({project.key})
          </option>
        ))}
      </select>
      <ChevronDown
        aria-hidden="true"
        className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary"
      />
    </div>
  );
}
