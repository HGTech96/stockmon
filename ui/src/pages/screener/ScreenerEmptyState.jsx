import { SearchX } from "lucide-react";
import { ScreenerRefreshButton } from "./ScreenerRefreshButton";

/**
 * Never-run state (`runAt === null`) -- distinct from the filtered-to-empty
 * state (`NoFilterResults`, shown inside the table when a real run's rows
 * are all filtered out).
 */
export function ScreenerEmptyState() {
  return (
    <div className="flex flex-col items-center gap-3.5 rounded-DEFAULT border border-border bg-surface px-6 py-16 text-center">
      <SearchX className="h-10 w-10 text-ink-faint" strokeWidth={1.4} />
      <h2 className="text-base font-bold">No screen yet</h2>
      <p className="max-w-[360px] text-[13.5px] leading-relaxed text-ink-muted">
        Run the screener to evaluate your universe, then come back here to see the results.
      </p>
      <ScreenerRefreshButton label="Run screener" />
    </div>
  );
}
