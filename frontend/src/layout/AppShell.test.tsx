import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("renders the primary nav landmark, the top bar slot, and the page content", () => {
    render(
      <AppShell topBar={<span>project selector goes here</span>}>
        <p>page content</p>
      </AppShell>
    );

    expect(screen.getByRole("navigation", { name: /primary/i })).toBeInTheDocument();
    expect(screen.getByText("project selector goes here")).toBeInTheDocument();
    expect(screen.getByText("page content")).toBeInTheDocument();
    expect(screen.getByText("Delivery Intelligence")).toBeInTheDocument();
  });

  it("marks the current Dashboard nav item with aria-current", () => {
    render(
      <AppShell topBar={<span>top bar</span>}>
        <p>content</p>
      </AppShell>
    );

    expect(screen.getByRole("link", { name: /dashboard/i })).toHaveAttribute(
      "aria-current",
      "page"
    );
  });
});
