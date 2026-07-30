import { AlertOctagon } from "lucide-react";
import type { RiskFinding } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ExplanationPanel } from "./ExplanationPanel";

/**
 * The single at-risk story card (ux-spec §4.1/§4.2 -- Von Restorff isolation:
 * the only saturated-red element on an otherwise calm page). Common
 * region + proximity (Gestalt): badge + why + evidence + actions inside one
 * bordered card so it reads as one object.
 */
export function RiskCard({ risk }: { risk: RiskFinding }) {
  const topReason = risk.reasons[0];

  return (
    <Card
      className="border-2 border-status-red-border bg-status-red-bg/40"
      data-testid="risk-card"
    >
      <CardContent className="flex flex-col gap-3 pt-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="red" className="gap-1.5">
            <AlertOctagon className="h-3.5 w-3.5" aria-hidden="true" />
            AT RISK
          </Badge>
          <h3 className="text-base font-bold text-text-primary">{risk.target_external_id}</h3>
          <span className="text-xs font-medium text-text-secondary">
            {risk.severity} severity · {Math.round(risk.confidence * 100)}% confidence
          </span>
        </div>

        {topReason && <p className="text-sm text-text-primary">{topReason}</p>}

        <ul aria-label="Evidence signals" className="flex flex-wrap gap-2">
          {risk.evidence_refs.map((ref) => (
            <li
              key={ref.signal_id}
              className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs font-medium text-text-secondary"
            >
              {ref.label}
            </li>
          ))}
        </ul>

        <div className="flex flex-wrap gap-2 pt-1">
          <ExplanationPanel risk={risk} />
        </div>
      </CardContent>
    </Card>
  );
}
