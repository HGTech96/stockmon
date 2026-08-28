import { Plus } from "lucide-react";

/**
 * @param {{ onClick: () => void }} props
 * Opens the add-stock modal. Raw-Tailwind styling matching RefreshButton's
 * secondary-button pattern (not the shadcn Button primitive), sitting
 * beside it above the dashboard table.
 */
export function AddStockButton({ onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 rounded-sm border border-border-strong bg-surface px-4 py-2.5 text-[13.5px] font-semibold text-ink transition-colors hover:bg-surface-hover active:translate-y-px"
    >
      <Plus className="h-3.5 w-3.5" strokeWidth={2.2} />
      Add stock
    </button>
  );
}
