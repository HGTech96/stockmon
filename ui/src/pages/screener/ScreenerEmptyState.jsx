import { SearchX } from "lucide-react";

/**
 * Never-run state (`runAt === null`) -- distinct from the filtered-to-empty
 * state (`NoFilterResults`, shown inside the table when a real run's rows
 * are all filtered out). No CTA button: the screener page never triggers
 * the batch job itself (CLAUDE.md) -- the job is a manual terminal script.
 */
export function ScreenerEmptyState() {
  return (
    <div className="flex flex-col items-center gap-3.5 rounded-DEFAULT border border-border bg-surface px-6 py-16 text-center">
      <SearchX className="h-10 w-10 text-ink-faint" strokeWidth={1.4} />
      <h2 className="text-base font-bold">No screen yet</h2>
      <p className="max-w-[360px] text-[13.5px] leading-relaxed text-ink-muted">
        Run <code className="rounded bg-surface-sunken px-1.5 py-0.5 text-[12.5px]">scripts/run_screener.py</code> from the terminal to
        evaluate your screener universe, then come back here to see the results.
      </p>
    </div>
  );
}
