import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StateBoundary } from "./StateBoundary";
import { ApiError } from "@/api/client";

describe("StateBoundary", () => {
  it("renders the loading fallback and marks the region busy while loading", () => {
    render(
      <StateBoundary
        state={{ isLoading: true, isError: false, error: null, refetch: vi.fn() }}
        loadingFallback={<p>loading skeleton</p>}
      >
        <p>content</p>
      </StateBoundary>
    );

    expect(screen.getByText("loading skeleton")).toBeInTheDocument();
    expect(screen.queryByText("content")).not.toBeInTheDocument();
    expect(screen.getByText("loading skeleton").parentElement).toHaveAttribute(
      "aria-busy",
      "true"
    );
  });

  it("renders a plain-language error with a retry action, and calls refetch on click", async () => {
    const refetch = vi.fn();
    const error = new ApiError(500, "boom", "Request failed with status 500");

    render(
      <StateBoundary
        state={{ isLoading: false, isError: true, error, refetch }}
        loadingFallback={<p>loading</p>}
      >
        <p>content</p>
      </StateBoundary>
    );

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Couldn't load this data");
    expect(alert).toHaveTextContent("Request failed with status 500");

    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("falls back to a generic message for a non-ApiError error", () => {
    render(
      <StateBoundary
        state={{ isLoading: false, isError: true, error: new Error("weird"), refetch: vi.fn() }}
        loadingFallback={<p>loading</p>}
      >
        <p>content</p>
      </StateBoundary>
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong loading this data.");
  });

  it("renders the empty state with title and description, never a blank screen", () => {
    render(
      <StateBoundary
        state={{ isLoading: false, isError: false, error: null, refetch: vi.fn() }}
        loadingFallback={<p>loading</p>}
        isEmpty
        emptyTitle="No sprints yet"
        emptyDescription="Load the demo dataset to get started."
      >
        <p>content</p>
      </StateBoundary>
    );

    expect(screen.getByText("No sprints yet")).toBeInTheDocument();
    expect(screen.getByText("Load the demo dataset to get started.")).toBeInTheDocument();
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("renders the optional emptyAction (e.g. a Connect CTA) under the empty-state description", () => {
    render(
      <StateBoundary
        state={{ isLoading: false, isError: false, error: null, refetch: vi.fn() }}
        loadingFallback={<p>loading</p>}
        isEmpty
        emptyAction={<button type="button">Connect a project</button>}
      >
        <p>content</p>
      </StateBoundary>
    );

    expect(screen.getByRole("button", { name: /connect a project/i })).toBeInTheDocument();
  });

  it("renders children on success", () => {
    render(
      <StateBoundary
        state={{ isLoading: false, isError: false, error: null, refetch: vi.fn() }}
        loadingFallback={<p>loading</p>}
      >
        <p>content</p>
      </StateBoundary>
    );

    expect(screen.getByText("content")).toBeInTheDocument();
  });
});
