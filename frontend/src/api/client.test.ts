import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  createConnection,
  createProject,
  detectRisks,
  getProjects,
  getRisks,
  getSprintHealth,
} from "./client";
import { makeProject, makeProjectListResponse, makeRiskFinding, makeSprintHealth } from "@/test/fixtures";

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("api/client", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    fetchMock.mockReset();
    vi.unstubAllGlobals();
  });

  it("getSprintHealth calls the documented path and returns parsed JSON", async () => {
    const health = makeSprintHealth();
    fetchMock.mockResolvedValueOnce(jsonResponse(health));

    const result = await getSprintHealth(1, "3");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/projects/1/sprints/3/health",
      expect.objectContaining({ headers: expect.any(Object) })
    );
    expect(result).toEqual(health);
  });

  it("getRisks calls the documented path", async () => {
    const risks = [makeRiskFinding()];
    fetchMock.mockResolvedValueOnce(jsonResponse(risks));

    const result = await getRisks(1);

    expect(fetchMock).toHaveBeenCalledWith("/api/projects/1/risks", expect.anything());
    expect(result).toEqual(risks);
  });

  it("detectRisks POSTs to the detect endpoint", async () => {
    const risks = [makeRiskFinding()];
    fetchMock.mockResolvedValueOnce(jsonResponse(risks));

    await detectRisks(1);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/projects/1/risks/detect",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("throws a network ApiError (status 0) when fetch rejects", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("failed to fetch"));

    await expect(getRisks(1)).rejects.toMatchObject({
      name: "ApiError",
      status: 0,
    });
  });

  it("throws an ApiError with the backend's detail on a non-OK JSON response", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ detail: "Project not found" }, { status: 404 })
    );

    await expect(getRisks(1)).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      detail: "Project not found",
    });
  });

  it("falls back to status text when a non-OK response isn't JSON", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response("<html>gateway timeout</html>", {
        status: 502,
        headers: { "Content-Type": "text/html" },
      })
    );

    await expect(getRisks(1)).rejects.toMatchObject({
      name: "ApiError",
      status: 502,
    });
  });

  it("returns undefined for a 204 No Content response", async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));

    const result = await detectRisks(1);

    expect(result).toBeUndefined();
  });

  it("getProjects calls GET /projects with no cursor by default", async () => {
    const response = makeProjectListResponse();
    fetchMock.mockResolvedValueOnce(jsonResponse(response));

    const result = await getProjects();

    expect(fetchMock).toHaveBeenCalledWith("/api/projects", expect.anything());
    expect(result).toEqual(response);
  });

  it("getProjects appends an encoded cursor when paginating", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(makeProjectListResponse()));

    await getProjects("cursor a/b");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/projects?cursor=cursor%20a%2Fb",
      expect.anything()
    );
  });

  it("createProject POSTs the key/name to /projects", async () => {
    const project = makeProject();
    fetchMock.mockResolvedValueOnce(jsonResponse(project));

    const result = await createProject({ key: "SCRUM", name: "Checkout Hardening" });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/projects",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ key: "SCRUM", name: "Checkout Hardening" }),
      })
    );
    expect(result).toEqual(project);
  });

  it("createConnection POSTs to /projects/{id}/connections", async () => {
    const connection = {
      id: 1,
      project_id: 1,
      source_type: "jira" as const,
      display_name: "Checkout Hardening",
      enabled: true,
    };
    fetchMock.mockResolvedValueOnce(jsonResponse(connection));

    const result = await createConnection(1, {
      source_type: "jira",
      display_name: "Checkout Hardening",
      base_url: "https://example.atlassian.net",
      project_ref: "SCRUM",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/projects/1/connections",
      expect.objectContaining({ method: "POST" })
    );
    expect(result).toEqual(connection);
  });

  it("ApiError carries status, detail, and message", () => {
    const err = new ApiError(500, "boom", "Request failed with status 500");
    expect(err.status).toBe(500);
    expect(err.detail).toBe("boom");
    expect(err.message).toBe("Request failed with status 500");
    expect(err).toBeInstanceOf(Error);
  });
});
