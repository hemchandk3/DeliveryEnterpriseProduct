import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { UseQueryResult } from "@tanstack/react-query";
import App from "./App";
import * as queries from "@/api/queries";
import type { RiskFinding, SprintHealth } from "@/api/types";

function mockQuery<T>(overrides: Partial<UseQueryResult<T>>): UseQueryResult<T> {
  return {
    data: undefined,
    isLoading: true,
    isError: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as UseQueryResult<T>;
}

describe("App", () => {
  it("mounts the app shell around the dashboard page", () => {
    vi.spyOn(queries, "useSprintHealth").mockReturnValue(mockQuery<SprintHealth>({}));
    vi.spyOn(queries, "useRiskReveal").mockReturnValue(mockQuery<RiskFinding[]>({}));

    render(<App />);

    expect(screen.getByRole("navigation", { name: /primary/i })).toBeInTheDocument();
    expect(screen.getByText("Delivery Intelligence")).toBeInTheDocument();
  });
});
