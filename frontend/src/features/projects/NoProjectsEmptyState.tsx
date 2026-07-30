import { FolderGit2 } from "lucide-react";
import { ConnectProjectDialog } from "./ConnectProjectDialog";

/**
 * First-run / empty state: no project connected yet (coordinator
 * scope-change requirement -- "a required design, not an afterthought").
 * This is what a brand-new tenant sees instead of any dashboard content --
 * no demo project, no sample data, just the real "you have nothing
 * connected" state and the one action that fixes it.
 */
export function NoProjectsEmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-24 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent/10 text-accent">
        <FolderGit2 className="h-7 w-7" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-1">
        <h1 className="text-lg font-bold text-text-primary">No projects connected yet</h1>
        <p className="max-w-md text-sm text-text-secondary">
          Connect a Jira project or GitHub repository and Delivery Intelligence will start
          reading real signals — sprint health, hidden risks, and the evidence behind them.
        </p>
      </div>
      <ConnectProjectDialog />
    </div>
  );
}
