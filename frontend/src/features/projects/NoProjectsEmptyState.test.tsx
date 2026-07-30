import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { NoProjectsEmptyState } from "./NoProjectsEmptyState";
import { createQueryWrapper } from "@/test/queryWrapper";

describe("NoProjectsEmptyState (required first-run design, never a demo project)", () => {
  it("explains why there's nothing and offers the connect CTA (Nielsen #10)", () => {
    const Wrapper = createQueryWrapper();
    render(<NoProjectsEmptyState />, { wrapper: Wrapper });

    expect(screen.getByRole("heading", { name: /no projects connected yet/i })).toBeInTheDocument();
    expect(screen.getByText(/connect a jira project or github repository/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /connect a project/i })).toBeInTheDocument();
  });
});
