import { useState, type FormEvent } from "react";
import { Plug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { useCreateConnection, useCreateProject } from "@/api/queries";
import { ApiError } from "@/api/client";
import type { ConnectionSourceType } from "@/api/types";

/**
 * The first-class "Connect external project / tools" entry point
 * (coordinator scope-change requirement). Calls the real, documented
 * contract (ARCHITECTURE.md §5.6 `POST /projects`, `POST
 * /projects/{id}/connections`) -- TODO(SCRUM-19): the backend for
 * connections management doesn't exist yet, so this is expected to surface
 * a real error from the API today. That is the honest behavior: never a
 * fake "connected" success, and never a client-invented project.
 */
export function ConnectProjectDialog() {
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState<ConnectionSourceType>("jira");
  const [baseUrl, setBaseUrl] = useState("");
  const [projectRef, setProjectRef] = useState("");

  const createProject = useCreateProject();
  const createConnection = useCreateConnection();

  const isSubmitting = createProject.isPending || createConnection.isPending;
  const submitError = createProject.error ?? createConnection.error;
  const succeeded = createConnection.isSuccess;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const project = await createProject.mutateAsync({ key, name });
      await createConnection.mutateAsync({
        projectId: project.id,
        source_type: sourceType,
        display_name: name,
        base_url: baseUrl,
        project_ref: projectRef,
      });
    } catch {
      // Already reflected in createProject.error / createConnection.error
      // below (both are honestly rendered) -- nothing further to do here.
      // Caught so a real backend failure never surfaces as an unhandled
      // promise rejection.
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="accent" size="sm">
          <Plug className="h-4 w-4" aria-hidden="true" />
          Connect a project
        </Button>
      </DialogTrigger>
      <DialogContent title="Connect a project" className="max-w-[480px]">
        <form onSubmit={(event) => void handleSubmit(event)} className="flex flex-col gap-4 p-6">
          <DialogDescription className="text-sm text-text-secondary">
            Link a Jira project or GitHub repository so Delivery Intelligence can start
            ingesting real signals for it.
          </DialogDescription>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="connect-key" className="text-sm font-medium text-text-primary">
              Project key
            </label>
            <input
              id="connect-key"
              required
              value={key}
              onChange={(event) => setKey(event.target.value)}
              placeholder="e.g. SCRUM"
              className="min-h-[36px] rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="connect-name" className="text-sm font-medium text-text-primary">
              Project name
            </label>
            <input
              id="connect-name"
              required
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Checkout Hardening"
              className="min-h-[36px] rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="connect-source" className="text-sm font-medium text-text-primary">
              Source
            </label>
            <select
              id="connect-source"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value as ConnectionSourceType)}
              className="min-h-[36px] rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-primary"
            >
              <option value="jira">Jira</option>
              <option value="github">GitHub</option>
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="connect-base-url" className="text-sm font-medium text-text-primary">
              Base URL
            </label>
            <input
              id="connect-base-url"
              required
              type="url"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              placeholder="https://your-org.atlassian.net"
              className="min-h-[36px] rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="connect-project-ref" className="text-sm font-medium text-text-primary">
              Project reference
            </label>
            <input
              id="connect-project-ref"
              required
              value={projectRef}
              onChange={(event) => setProjectRef(event.target.value)}
              placeholder="Jira project key or GitHub owner/repo"
              className="min-h-[36px] rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-primary"
            />
          </div>

          {submitError != null && (
            <p role="alert" className="text-sm text-status-red">
              {submitError instanceof ApiError
                ? submitError.message
                : "Couldn't connect this project. Please try again."}
            </p>
          )}
          {succeeded && (
            <p role="status" className="text-sm text-status-green">
              Connected. It will appear in the project selector shortly.
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="submit" variant="accent" disabled={isSubmitting}>
              {isSubmitting ? "Connecting…" : "Connect"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
