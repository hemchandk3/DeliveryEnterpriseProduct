import type { ReactNode } from "react";
import { AlertTriangle, Inbox } from "lucide-react";
import { ApiError } from "@/api/client";
import { Button } from "@/components/ui/button";

export type QueryLikeState = {
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
};

interface StateBoundaryProps {
  state: QueryLikeState;
  /** Renders the loading skeleton -- a skeleton of the real layout, not a bare spinner. */
  loadingFallback: ReactNode;
  /** True when the data loaded successfully but is empty. */
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  children: ReactNode;
}

/**
 * Implements the universal state model required by ux-spec §3 / SCRUM-16 AC
 * ("Given loading/error/empty, Then distinct states -- never blank/silent
 * fail"): loading, empty, error, and success are always visually and
 * programmatically distinct -- never a blank screen.
 */
export function StateBoundary({
  state,
  loadingFallback,
  isEmpty = false,
  emptyTitle = "Nothing here yet",
  emptyDescription = "There's no data to show right now.",
  children,
}: StateBoundaryProps) {
  if (state.isLoading) {
    return <div aria-busy="true">{loadingFallback}</div>;
  }

  if (state.isError) {
    const message =
      state.error instanceof ApiError
        ? state.error.message
        : "Something went wrong loading this data.";
    return (
      <div
        role="alert"
        className="flex flex-col items-start gap-3 rounded-lg border border-status-red-border bg-status-red-bg p-4"
      >
        <div className="flex items-center gap-2 font-semibold text-status-red">
          <AlertTriangle className="h-5 w-5" aria-hidden="true" />
          <span>Couldn't load this data</span>
        </div>
        <p className="text-sm text-text-primary">{message}</p>
        <Button variant="outline" size="sm" onClick={() => state.refetch()}>
          Try again
        </Button>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="flex flex-col items-start gap-2 rounded-lg border border-slate-200 bg-subtle p-4 text-text-secondary">
        <div className="flex items-center gap-2 font-semibold text-text-primary">
          <Inbox className="h-5 w-5" aria-hidden="true" />
          <span>{emptyTitle}</span>
        </div>
        <p className="text-sm">{emptyDescription}</p>
      </div>
    );
  }

  return <>{children}</>;
}
