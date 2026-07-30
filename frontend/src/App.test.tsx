import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { UseQueryResult } from "@tanstack/react-query";
import App from "./App";
import * as queries from "@/api/queries";
import type { ProjectListResponse, RiskFinding, SprintHealth } from "@/api/types";
import { createQueryWrapper } from "@/test/queryWrapper";
import { makeProject, makeProjectListResponse, makeSprintHealth } from "@/test/fixtures";

function mockQuery<T>(overrides: Partial<UseQueryResult<T>>): UseQueryResult<T> {
  return {
    data: undefined,
    isLoading: false,
    isError: false,
    isSuccess: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as UseQueryResult<T>;
}

function renderApp() {
  const Wrapper = createQueryWrapper();
  return render(<App />, { wrapper: Wrapper });
}

describe("App (project selection is the source of truth -- no hardcoded/demo project)", () => {
  it("shows loading state while GET /projects is in flight, with no dashboard content", () => {
    vi.spyOn(queries, "useProjects").mockReturnValue(
      mockQuery<ProjectListResponse>({ isLoading: true })
    );

    renderApp();

    expect(screen.queryByText(/on track/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /no projects connected yet/i })).not.toBeInTheDocument();
  });

  it("shows the required first-run empty state when the tenant has zero connected projects, never a fake project", () => {
    vi.spyOn(queries, "useProjects").mockReturnValue(
      mockQuery<ProjectListResponse>({
        isSuccess: true,
        data: makeProjectListResponse({ items: [] }),
      })
    );

    renderApp();

    expect(screen.getByRole("heading", { name: /no projects connected yet/i })).toBeInTheDocument();
    // Only the empty state's own CTA renders -- the top bar doesn't duplicate it.
    expect(screen.getAllByRole("button", { name: /connect a project/i })).toHaveLength(1);
  });

  it("auto-selects the tenant's first real project and renders its dashboard by its own sprint id", () => {
    const project = makeProject({ id: 42, key: "SCRUM", name: "Checkout Hardening" });
    vi.spyOn(queries, "useProjects").mockReturnValue(
      mockQuery<ProjectListResponse>({
        isSuccess: true,
        data: makeProjectListResponse({ items: [project] }),
      })
    );
    const useSprintHealthSpy = vi
      .spyOn(queries, "useSprintHealth")
      .mockReturnValue(mockQuery<SprintHealth>({ data: makeSprintHealth() }));
    vi.spyOn(queries, "useRiskReveal").mockReturnValue(mockQuery<RiskFinding[]>({ data: [] }));

    renderApp();

    expect(useSprintHealthSpy).toHaveBeenCalledWith(42, "3");
    expect(screen.getByRole("option", { name: /checkout hardening \(scrum\)/i })).toBeInTheDocument();
  });

  it("honestly reports when a connected project has no computed sprint health yet (not a blank dashboard)", () => {
    const project = makeProject({ id: 5, name: "New Project", latest_health: null });
    vi.spyOn(queries, "useProjects").mockReturnValue(
      mockQuery<ProjectListResponse>({
        isSuccess: true,
        data: makeProjectListResponse({ items: [project] }),
      })
    );

    renderApp();

    expect(screen.getByText(/no sprint health computed yet/i)).toBeInTheDocument();
  });

  it("surfaces a distinct error state if GET /projects fails, never a blank screen", () => {
    vi.spyOn(queries, "useProjects").mockReturnValue(
      mockQuery<ProjectListResponse>({ isError: true, error: new Error("down") })
    );

    renderApp();

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
