import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConnectProjectDialog } from "./ConnectProjectDialog";
import * as client from "@/api/client";
import { ApiError } from "@/api/client";
import { createQueryWrapper } from "@/test/queryWrapper";
import { makeProject } from "@/test/fixtures";

async function openDialog() {
  await userEvent.click(screen.getByRole("button", { name: /connect a project/i }));
  return screen.findByRole("dialog");
}

describe("ConnectProjectDialog (first-class 'connect external project' entry point)", () => {
  it("is closed by default and opens the connect form on trigger click", async () => {
    const Wrapper = createQueryWrapper();
    render(<ConnectProjectDialog />, { wrapper: Wrapper });

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    const dialog = await openDialog();
    expect(within(dialog).getByText("Connect a project")).toBeInTheDocument();
  });

  it("requires the key, name, base URL, and project reference fields", async () => {
    const Wrapper = createQueryWrapper();
    render(<ConnectProjectDialog />, { wrapper: Wrapper });
    await openDialog();

    expect(screen.getByLabelText(/project key/i)).toBeRequired();
    expect(screen.getByLabelText(/project name/i)).toBeRequired();
    expect(screen.getByLabelText(/base url/i)).toBeRequired();
    expect(screen.getByLabelText(/project reference/i)).toBeRequired();
  });

  it("wires the real create-project + create-connection calls and surfaces a genuine backend error honestly (SCRUM-19 not built yet)", async () => {
    const createProjectSpy = vi
      .spyOn(client, "createProject")
      .mockRejectedValue(new ApiError(404, "Not Found", "Request failed with status 404"));

    const Wrapper = createQueryWrapper();
    render(<ConnectProjectDialog />, { wrapper: Wrapper });
    await openDialog();

    await userEvent.type(screen.getByLabelText(/project key/i), "SCRUM");
    await userEvent.type(screen.getByLabelText(/project name/i), "Checkout Hardening");
    await userEvent.type(screen.getByLabelText(/base url/i), "https://example.atlassian.net");
    await userEvent.type(screen.getByLabelText(/project reference/i), "SCRUM");
    await userEvent.click(screen.getByRole("button", { name: /^connect$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Request failed with status 404");
    expect(createProjectSpy).toHaveBeenCalledWith({ key: "SCRUM", name: "Checkout Hardening" });
  });

  it("shows a genuine success state (never faked) once both calls succeed", async () => {
    const project = makeProject({ id: 7, key: "PAY", name: "Payments Platform" });
    vi.spyOn(client, "createProject").mockResolvedValue(project);
    vi.spyOn(client, "createConnection").mockResolvedValue({
      id: 1,
      project_id: 7,
      source_type: "jira",
      display_name: "Payments Platform",
      enabled: true,
    });

    const Wrapper = createQueryWrapper();
    render(<ConnectProjectDialog />, { wrapper: Wrapper });
    await openDialog();

    await userEvent.type(screen.getByLabelText(/project key/i), "PAY");
    await userEvent.type(screen.getByLabelText(/project name/i), "Payments Platform");
    await userEvent.type(screen.getByLabelText(/base url/i), "https://example.atlassian.net");
    await userEvent.type(screen.getByLabelText(/project reference/i), "PAY");
    await userEvent.click(screen.getByRole("button", { name: /^connect$/i }));

    expect(await screen.findByRole("status")).toHaveTextContent(/connected/i);
  });
});
