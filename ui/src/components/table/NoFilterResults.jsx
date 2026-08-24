import { SearchX } from "lucide-react";

/**
 * @param {{ colSpan: number, onReset: () => void }} props
 * Full-width row shown in place of the body rows when active filters
 * exclude every row -- distinct from a table's genuinely-empty state
 * (e.g. Portfolio's `EmptyState`, which fires on `!hasTrades` and replaces
 * the whole table instead of rendering inside it).
 */
export function NoFilterResults({ colSpan, onReset }) {
  return (
    <tr>
      <td colSpan={colSpan} className="px-4.5 py-14 text-center">
        <div className="flex flex-col items-center gap-2.5">
          <SearchX className="h-7 w-7 text-ink-faint" strokeWidth={1.4} />
          <p className="text-[13.5px] text-ink-muted">No stocks match your filters</p>
          <button type="button" onClick={onReset} className="text-[12.5px] font-semibold text-accent hover:text-accent-ink">
            Clear filters
          </button>
        </div>
      </td>
    </tr>
  );
}
