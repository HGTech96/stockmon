import { Inbox, Plus } from "lucide-react";

/**
 * @param {{ onAddTrade: () => void }} props
 * No-trades state per the reference: icon, heading, explanatory copy,
 * "Add trade" button wired to open the modal.
 */
export function EmptyState({ onAddTrade }) {
  return (
    <div className="flex flex-col items-center gap-3.5 rounded-DEFAULT border border-border bg-surface px-6 py-16 text-center">
      <Inbox className="h-10 w-10 text-ink-faint" strokeWidth={1.4} />
      <h2 className="text-base font-bold">No trades recorded yet</h2>
      <p className="max-w-[360px] text-[13.5px] leading-relaxed text-ink-muted">
        Your watchlist has stocks, but you haven&rsquo;t logged any trades. Add your first trade to start tracking positions, profit
        and loss, and progress toward your hard caps.
      </p>
      <button
        type="button"
        onClick={onAddTrade}
        className="mt-1 inline-flex items-center gap-1.5 rounded-lg border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white hover:bg-accent-ink"
      >
        <Plus className="h-[15px] w-[15px]" strokeWidth={2} />
        Add trade
      </button>
    </div>
  );
}
