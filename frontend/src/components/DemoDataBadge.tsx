import { Badge } from "@/components/ui/badge";

/**
 * Persistent "Demo data" indicator (SCRUM-16 AC "Given demo provenance,
 * Then persistent Demo data indicator"; ux-spec §3 universal state 5).
 *
 * KNOWN GAP (see .env.example): `SprintHealth`/`RiskFinding` do not
 * currently surface `Signal.provenance` on the wire, so this cannot yet
 * read the backend's own truth per-request -- it renders a build-time
 * label (`VITE_DATA_PROVENANCE`) instead. Flagged for architect/developer
 * to add real per-response provenance; do not remove this comment until
 * that lands and this component is wired to it.
 */
export function DemoDataBadge() {
  const provenance = import.meta.env.VITE_DATA_PROVENANCE ?? "demo";
  if (provenance !== "demo") {
    return null;
  }
  return (
    <Badge variant="info" className="shrink-0">
      Demo data — curated, not live
    </Badge>
  );
}
