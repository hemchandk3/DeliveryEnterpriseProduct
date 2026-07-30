import type { UseQueryResult } from "@tanstack/react-query";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import type { RiskFinding } from "@/api/types";
import { StateBoundary } from "@/components/StateBoundary";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskCard } from "./RiskCard";

/**
 * The reveal (ux-spec §4.2, "the heart of the screen"): progressive
 * disclosure, not a state swap -- the green surface (`SprintHealthPanel`)
 * stays on screen while this renders alongside it in the same view
 * (SCRUM-16 AC "contradiction visible in one view"). Closes the Gulf of
 * Evaluation (Norman): the user sees the true system state, not a
 * flattering summary.
 *
 * `role="status"`/`aria-live="polite"` on the outer section is the
 * [Blocker] fix from ux-spec §4.3: the reveal must be announced to
 * assistive tech (WCAG 4.1.3 Status Messages). The section itself is
 * always present in the DOM (loading -> empty/found), so content changes
 * inside it are announced -- nothing here is ever a silent state change.
 */
export function RiskReveal({ risksQuery }: { risksQuery: UseQueryResult<RiskFinding[]> }) {
  const risks = risksQuery.data ?? [];

  return (
    <section aria-live="polite" role="status" className="flex flex-col gap-4">
      <StateBoundary
        state={{
          isLoading: risksQuery.isLoading,
          isError: risksQuery.isError,
          error: risksQuery.error,
          refetch: () => void risksQuery.refetch(),
        }}
        loadingFallback={
          <div className="flex items-center gap-3 rounded-lg border border-border bg-surface p-4">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-4 w-64" />
          </div>
        }
      >
        {risks.length === 0 ? (
          <div className="flex items-center gap-3 rounded-lg border border-status-green-border bg-status-green-bg p-4 text-status-green">
            <ShieldCheck className="h-5 w-5 shrink-0" aria-hidden="true" />
            <p className="text-sm font-semibold">
              Delivery Intelligence found no hidden risks in this sprint.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 rounded-lg border border-status-red-border bg-status-red-bg p-4 text-status-red">
              <ShieldAlert className="h-6 w-6 shrink-0" aria-hidden="true" />
              <h2 className="text-base font-bold">
                Delivery Intelligence found {risks.length}{" "}
                {risks.length === 1 ? "hidden risk" : "hidden risks"} the board doesn't show
              </h2>
            </div>
            <div className="flex flex-col gap-4">
              {risks.map((risk) => (
                <RiskCard key={risk.target_external_id} risk={risk} />
              ))}
            </div>
          </div>
        )}
      </StateBoundary>
    </section>
  );
}
