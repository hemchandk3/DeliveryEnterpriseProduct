import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { useCreateConnection, useCreateProject, useProjects, useRiskReveal, useSprintHealth } from "./queries";
import * as client from "./client";
import { makeProject, makeProjectListResponse, makeRiskFinding, makeSprintHealth } from "@/test/fixtures";

function wrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("api/queries", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("useSprintHealth fetches and returns sprint health", async () => {
    const health = makeSprintHealth();
    vi.spyOn(client, "getSprintHealth").mockResolvedValue(health);

    const { result } = renderHook(() => useSprintHealth(1, "3"), { wrapper: wrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(health);
    expect(client.getSprintHealth).toHaveBeenCalledWith(1, "3");
  });

  it("useRiskReveal returns risks as-is when the list is non-empty (no detect trigger)", async () => {
    const risks = [makeRiskFinding()];
    vi.spyOn(client, "getRisks").mockResolvedValue(risks);
    const detectSpy = vi.spyOn(client, "detectRisks").mockResolvedValue(risks);

    const { result } = renderHook(() => useRiskReveal(1), { wrapper: wrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(risks);
    expect(detectSpy).not.toHaveBeenCalled();
  });

  it("useRiskReveal triggers POST /risks/detect exactly once when the list comes back empty", async () => {
    const risks = [makeRiskFinding()];
    const getRisksSpy = vi
      .spyOn(client, "getRisks")
      .mockResolvedValueOnce([]) // first read: empty
      .mockResolvedValueOnce(risks); // refetch after detect: populated
    const detectSpy = vi.spyOn(client, "detectRisks").mockResolvedValue(risks);

    const { result } = renderHook(() => useRiskReveal(1), { wrapper: wrapper() });

    await waitFor(() => expect(detectSpy).toHaveBeenCalledTimes(1));
    expect(detectSpy).toHaveBeenCalledWith(1);

    await waitFor(() => expect(result.current.data).toEqual(risks));
    expect(getRisksSpy).toHaveBeenCalledTimes(2);
  });

  it("useProjects fetches the tenant's real project list", async () => {
    const response = makeProjectListResponse();
    vi.spyOn(client, "getProjects").mockResolvedValue(response);

    const { result } = renderHook(() => useProjects(), { wrapper: wrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(response);
  });

  it("useCreateProject calls the real POST /projects and invalidates the project list on success", async () => {
    const project = makeProject();
    vi.spyOn(client, "createProject").mockResolvedValue(project);
    const getProjectsSpy = vi.spyOn(client, "getProjects").mockResolvedValue(makeProjectListResponse());

    const { result } = renderHook(
      () => ({ create: useCreateProject(), list: useProjects() }),
      { wrapper: wrapper() }
    );
    await waitFor(() => expect(result.current.list.isSuccess).toBe(true));
    getProjectsSpy.mockClear();

    result.current.create.mutate({ key: "SCRUM", name: "Checkout Hardening" });

    await waitFor(() => expect(result.current.create.isSuccess).toBe(true));
    expect(result.current.create.data).toEqual(project);
    await waitFor(() => expect(getProjectsSpy).toHaveBeenCalled());
  });

  it("useCreateConnection calls the real POST /projects/{id}/connections with the project id folded in", async () => {
    const connection = {
      id: 1,
      project_id: 9,
      source_type: "github" as const,
      display_name: "svc-checkout",
      enabled: true,
    };
    const createConnectionSpy = vi.spyOn(client, "createConnection").mockResolvedValue(connection);

    const { result } = renderHook(() => useCreateConnection(), { wrapper: wrapper() });

    result.current.mutate({
      projectId: 9,
      source_type: "github",
      display_name: "svc-checkout",
      base_url: "https://github.com",
      project_ref: "org/svc-checkout",
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(createConnectionSpy).toHaveBeenCalledWith(9, {
      source_type: "github",
      display_name: "svc-checkout",
      base_url: "https://github.com",
      project_ref: "org/svc-checkout",
    });
  });
});
