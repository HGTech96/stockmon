import { Inbox } from "lucide-react";

/**
 * No-trades state. Read-only page -- no CTA button here; trades are added
 * from the Portfolio page.
 */
export function EmptyState() {
  return (
    <div className="flex flex-col items-center gap-3.5 rounded-DEFAULT border border-border bg-surface px-6 py-16 text-center">
      <Inbox className="h-10 w-10 text-ink-faint" strokeWidth={1.4} />
      <h2 className="text-base font-bold">No trades recorded yet</h2>
      <p className="max-w-[360px] text-[13.5px] leading-relaxed text-ink-muted">
        Once you record buys and sells from the Portfolio page, they&rsquo;ll show up here with realized profit and loss.
      </p>
    </div>
  );
}
