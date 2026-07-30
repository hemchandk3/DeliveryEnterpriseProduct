import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { UseQueryResult } from "@tanstack/react-query";
import { DashboardPage } from "./DashboardPage";
import * as queries from "@/api/queries";
import type { RiskFinding, SprintHealth } from "@/api/types";
import { makeRiskFinding, makeSprintHealth } from "@/test/fixtures";

function mockQuery<T>(overrides: Partial<UseQueryResult<T>>): UseQueryResult<T> {
  return {
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as UseQueryResult<T>;
}

describe("DashboardPage (SCRUM-16 -- green surface + hidden-risk reveal, same view)", () => {
  it("fetches health and risks for the given projectId/sprintId (sourced from the selected Project, never hardcoded)", () => {
    const useSprintHealthSpy = vi
      .spyOn(queries, "useSprintHealth")
      .mockReturnValue(mockQuery<SprintHealth>({ isLoading: true }));
    const useRiskRevealSpy = vi
      .spyOn(queries, "useRiskReveal")
      .mockReturnValue(mockQuery<RiskFinding[]>({ isLoading: true }));

    render(<DashboardPage projectId={7} sprintId="9" />);

    expect(useSprintHealthSpy).toHaveBeenCalledWith(7, "9");
    expect(useRiskRevealSpy).toHaveBeenCalledWith(7);
  });

  it("shows loading skeletons for both the health surface and the reveal while data is in flight", () => {
    vi.spyOn(queries, "useSprintHealth").mockReturnValue(
      mockQuery<SprintHealth>({ isLoading: true })
    );
    vi.spyOn(queries, "useRiskReveal").mockReturnValue(
      mockQuery<RiskFinding[]>({ isLoading: true })
    );

    render(<DashboardPage projectId={1} sprintId="3" />);

    expect(screen.queryByText(/on track/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/hidden risk/i)).not.toBeInTheDocument();
    expect(screen.getByText("Sprint health")).toBeInTheDocument(); // header fallback title
  });

  it("renders the green surface AND the red reveal together in one view (the contradiction is the point)", () => {
    const health = makeSprintHealth({ status: "green" });
    const risks = [makeRiskFinding()];
    vi.spyOn(queries, "useSprintHealth").mockReturnValue(mockQuery<SprintHealth>({ data: health }));
    vi.spyOn(queries, "useRiskReveal").mockReturnValue(mockQuery<RiskFinding[]>({ data: risks }));

    render(<DashboardPage projectId={1} sprintId="3" />);

    // Green surface still visible...
    expect(screen.getByRole("heading", { name: /on track/i })).toBeInTheDocument();
    // ...at the same time as the hidden-risk reveal (SCRUM-16 AC).
    expect(
      screen.getByRole("heading", { name: /found 1 hidden risk the board doesn't show/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "SCRUM-42" })).toBeInTheDocument();
  });

  it("renders the sprint name and elapsed/total days from the real response in the header", () => {
    const health = makeSprintHealth({
      name: "Sprint 3 — Checkout Hardening",
      elapsed_days: 11,
      total_days: 14,
    });
    vi.spyOn(queries, "useSprintHealth").mockReturnValue(mockQuery<SprintHealth>({ data: health }));
    vi.spyOn(queries, "useRiskReveal").mockReturnValue(mockQuery<RiskFinding[]>({ data: [] }));

    render(<DashboardPage projectId={1} sprintId="3" />);

    expect(screen.getByRole("heading", { name: "Sprint 3 — Checkout Hardening" })).toBeInTheDocument();
    // "Day 11 of 14" appears twice (page sub-heading + the Days-remaining
    // metric card's sublabel) -- assert both real occurrences are present.
    expect(screen.getAllByText("Day 11 of 14")).toHaveLength(2);
  });

  it("surfaces a health-load error distinctly from the reveal region", () => {
    vi.spyOn(queries, "useSprintHealth").mockReturnValue(
      mockQuery<SprintHealth>({ isError: true, error: new Error("down") })
    );
    vi.spyOn(queries, "useRiskReveal").mockReturnValue(mockQuery<RiskFinding[]>({ data: [] }));

    render(<DashboardPage projectId={1} sprintId="3" />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
