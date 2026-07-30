const KIND_LABELS: Record<string, string> = {
  "jira/issue": "Jira issue",
  "github/pr": "GitHub PR",
  "github/commit": "GitHub commit",
};

export interface CitationRowProps {
  index: number;
  /** The claim/fact itself, verbatim from the backend (never re-authored client-side). */
  claim: string;
  /** Signal kind, e.g. "jira/issue" -- present only for evidence-pointer rows. */
  kind?: string;
  /** e.g. "Signal #42" -- the exact stored record this row points at. */
  sourceDetail?: string;
}

/**
 * One scannable evidence/reason row (ux-spec §5.2 "the trust unit" --
 * Nielsen #6 recognition over recall: the reader never has to remember or
 * reconstruct the data). Today this renders the Detect engine's own
 * `reasons[]` / `evidence_refs[]` (see ExplanationPanel.tsx TODO(SCRUM-11)
 * comment) -- the exact field-path + quoted-value + deep-link version
 * (ARCHITECTURE.md §5.3 `Citation`) replaces this once SCRUM-11 ships.
 */
export function CitationRow({ index, claim, kind, sourceDetail }: CitationRowProps) {
  return (
    <li className="flex gap-3 border-b border-border py-3 last:border-b-0">
      <span
        aria-hidden="true"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-subtle text-xs font-semibold text-text-secondary"
      >
        {index}
      </span>
      <div className="flex min-w-0 flex-col gap-1">
        {kind && (
          <span className="inline-flex w-fit items-center rounded border border-border bg-subtle px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-text-secondary">
            {KIND_LABELS[kind] ?? kind}
          </span>
        )}
        <p className="text-sm text-text-primary">{claim}</p>
        {sourceDetail && (
          /* #475569 on #F1F5F9-equivalent subtle bg -- the corrected
             contrast value from ux-spec §5.3 Medium finding. */
          <p className="font-mono text-xs text-text-secondary">{sourceDetail}</p>
        )}
      </div>
    </li>
  );
}
