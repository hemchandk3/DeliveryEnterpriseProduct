import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { UseQueryResult } from "@tanstack/react-query";
import { ProjectSelector } from "./ProjectSelector";
import type { ProjectListResponse } from "@/api/types";
import { makeProject, makeProjectListResponse } from "@/test/fixtures";

function mockQuery(
  overrides: Partial<UseQueryResult<ProjectListResponse>>
): UseQueryResult<ProjectListResponse> {
  return {
    data: undefined,
    isLoading: false,
    isError: false,
    error: null,
    isSuccess: false,
    refetch: vi.fn(),
    ...overrides,
  } as unknown as UseQueryResult<ProjectListResponse>;
}

describe("ProjectSelector (real, tenant-scoped project list -- never a fake/demo list)", () => {
  it("shows a loading placeholder while GET /projects is in flight", () => {
    render(
      <ProjectSelector
        projectsQuery={mockQuery({ isLoading: true })}
        selectedProjectId={null}
        onSelect={vi.fn()}
      />
    );
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });

  it("surfaces a distinct error state, not a silent failure", () => {
    render(
      <ProjectSelector
        projectsQuery={mockQuery({ isError: true, error: new Error("down") })}
        selectedProjectId={null}
        onSelect={vi.fn()}
      />
    );
    expect(screen.getByText(/couldn't load projects/i)).toBeInTheDocument();
  });

  it("renders nothing when the tenant has no connected projects (parent renders the first-run state)", () => {
    const { container } = render(
      <ProjectSelector
        projectsQuery={mockQuery({ isSuccess: true, data: makeProjectListResponse({ items: [] }) })}
        selectedProjectId={null}
        onSelect={vi.fn()}
      />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("lists every real connected project by name and key, and calls onSelect on change", async () => {
    const projects = [
      makeProject({ id: 1, name: "Checkout Hardening", key: "SCRUM" }),
      makeProject({ id: 2, name: "Payments Platform", key: "PAY" }),
    ];
    const onSelect = vi.fn();
    render(
      <ProjectSelector
        projectsQuery={mockQuery({ isSuccess: true, data: makeProjectListResponse({ items: projects }) })}
        selectedProjectId={1}
        onSelect={onSelect}
      />
    );

    const select = screen.getByRole("combobox", { name: /project/i });
    expect(screen.getByRole("option", { name: /checkout hardening \(scrum\)/i })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /payments platform \(pay\)/i })).toBeInTheDocument();

    await userEvent.selectOptions(select, "2");
    expect(onSelect).toHaveBeenCalledWith(2);
  });
});
