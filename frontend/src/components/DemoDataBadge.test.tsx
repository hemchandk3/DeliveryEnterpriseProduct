import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DemoDataBadge } from "./DemoDataBadge";

describe("DemoDataBadge", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("renders the persistent demo-data indicator by default", () => {
    render(<DemoDataBadge />);
    expect(screen.getByText(/demo data — curated, not live/i)).toBeInTheDocument();
  });

  it("renders nothing when provenance is explicitly not demo", () => {
    vi.stubEnv("VITE_DATA_PROVENANCE", "live");
    const { container } = render(<DemoDataBadge />);
    expect(container).toBeEmptyDOMElement();
  });
});
