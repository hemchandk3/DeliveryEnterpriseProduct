import { CheckCircle2, AlertCircle, AlertTriangle } from "lucide-react";
import type { SprintHealth } from "@/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBreakdown } from "./StatusBreakdown";

const STATUS_COPY: Record<SprintHealth["status"], { label: string; icon: typeof CheckCircle2 }> = {
  green: { label: "On track", icon: CheckCircle2 },
  amber: { label: "Needs attention", icon: AlertTriangle },
  red: { label: "At risk", icon: AlertCircle },
};

const STATUS_CLASSES: Record<SprintHealth["status"], string> = {
  green: "bg-status-green-bg text-status-green border-status-green-border",
  amber: "bg-status-amber-bg text-status-amber border-status-amber-border",
  red: "bg-status-red-bg text-status-red border-status-red-border",
};

/**
 * The "green surface" (ux-spec §4.1): health banner + 4 metric cards +
 * status breakdown. Every figure is read straight off `SprintHealth`
 * (ux-spec §4.3 Medium finding "Metric internal consistency" -- never a
 * hand-typed number that could contradict a sibling figure).
 */
export function SprintHealthPanel({ health }: { health: SprintHealth }) {
  const { label, icon: Icon } = STATUS_COPY[health.status];
  const daysRemaining = Math.max(health.total_days - health.elapsed_days, 0);
  const totalIssues = health.issues_done + health.issues_in_progress + health.issues_todo;

  return (
    <section aria-labelledby="sprint-health-heading" className="flex flex-col gap-4">
      <div
        className={`flex flex-wrap items-center gap-3 rounded-lg border p-4 ${STATUS_CLASSES[health.status]}`}
      >
        <Icon className="h-6 w-6 shrink-0" aria-hidden="true" />
        <h2 id="sprint-health-heading" className="text-lg font-bold uppercase tracking-wide">
          {label}
        </h2>
        <details className="ml-auto">
          <summary className="cursor-pointer list-none rounded-md px-2 py-1 text-sm font-semibold underline decoration-dotted underline-offset-4 focus:outline-none">
            Health {health.score}/100
          </summary>
          <div className="mt-2 min-w-[220px] rounded-md border border-border bg-surface p-3 text-xs font-normal text-text-secondary">
            <p className="mb-1 font-semibold text-text-primary">What makes up this score</p>
            <ul className="space-y-1">
              {health.factors.map((factor) => (
                <li key={factor.name} className="flex justify-between gap-4">
                  <span className="capitalize">{factor.name.replaceAll("_", " ")}</span>
                  <span>{factor.contribution.toFixed(1)} pts</span>
                </li>
              ))}
            </ul>
          </div>
        </details>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Health score" value={`${health.score}/100`} />
        <MetricCard
          label="Points burned"
          value={`${health.points_done} of ${health.points_total} pts`}
        />
        <MetricCard
          label="Issues complete"
          value={`${health.issues_done} of ${totalIssues}`}
        />
        <MetricCard
          label="Days remaining"
          value={`${daysRemaining} of ${health.total_days}`}
          sublabel={`Day ${health.elapsed_days} of ${health.total_days}`}
        />
      </div>

      <StatusBreakdown
        done={health.issues_done}
        inProgress={health.issues_in_progress}
        todo={health.issues_todo}
      />
    </section>
  );
}

function MetricCard({
  label,
  value,
  sublabel,
}: {
  label: string;
  value: string;
  sublabel?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-1">
        {/* text-secondary, not the failing #94A3B8 (ux-spec §4.3 High finding) */}
        <CardTitle as="h3" className="text-text-secondary">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold text-text-primary">{value}</p>
        {sublabel && <p className="mt-1 text-xs text-text-secondary">{sublabel}</p>}
      </CardContent>
    </Card>
  );
}
