import { ChevronDown, ChevronsUpDown, ChevronUp } from "lucide-react";

/**
 * @param {{
 *   label: string, align?: "left"|"right", sortKey: string,
 *   sort: import('../../lib/tableViewState').SortState|null,
 *   onSort: (key: string) => void, style?: object,
 * }} props
 * Clickable, keyboard-focusable <th> that cycles this column's sort state
 * on click or Enter/Space -- same interaction pattern as the clickable
 * StockRow/PositionRow. Shows a faint neutral icon when this column isn't
 * the active sort, a solid up/down chevron when it is.
 */
export function SortableHeaderCell({ label, align = "left", sortKey, sort, onSort, style }) {
  const isActive = sort?.key === sortKey;
  const direction = isActive ? sort.direction : null;

  return (
    <th
      className={`cursor-pointer px-4.5 py-2.5 text-[11.5px] font-bold tracking-wide text-ink-muted uppercase select-none hover:text-ink ${
        align === "right" ? "text-right" : "text-left"
      }`}
      style={style}
      tabIndex={0}
      aria-sort={direction === "asc" ? "ascending" : direction === "desc" ? "descending" : "none"}
      onClick={() => onSort(sortKey)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSort(sortKey);
        }
      }}
    >
      <span className={`inline-flex items-center gap-1 ${align === "right" ? "flex-row-reverse" : ""}`}>
        {label}
        {direction === "asc" && <ChevronUp className="h-3 w-3" strokeWidth={2.5} />}
        {direction === "desc" && <ChevronDown className="h-3 w-3" strokeWidth={2.5} />}
        {!direction && <ChevronsUpDown className="h-3 w-3 opacity-30" strokeWidth={2} />}
      </span>
    </th>
  );
}
