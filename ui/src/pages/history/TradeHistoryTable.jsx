import { TradeHistoryRow } from "./TradeHistoryRow";

const HEADERS = [
  { label: "Date", align: "left" },
  { label: "Stock", align: "left" },
  { label: "Action", align: "left" },
  { label: "Shares", align: "right" },
  { label: "Price", align: "right" },
  { label: "Total", align: "right" },
  { label: "Realized P/L", align: "right" },
  { label: "", align: "right" },
];

/**
 * @param {{
 *   trades: import('../../api/types').TradeHistoryEntry[],
 *   onEdit: (trade: import('../../api/types').TradeHistoryEntry) => void,
 *   onDelete: (trade: import('../../api/types').TradeHistoryEntry) => void,
 * }} props
 * Table shell + one <TradeHistoryRow/> per entry, in array order -- the
 * API sends trades newest-first already, no client sorting.
 */
export function TradeHistoryTable({ trades, onEdit, onDelete }) {
  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-sunken">
              {HEADERS.map((h) => (
                <th
                  key={h.label}
                  className={`px-4.5 py-2.5 text-[11.5px] font-bold tracking-wide text-ink-muted uppercase ${
                    h.align === "right" ? "text-right" : "text-left"
                  }`}
                >
                  {h.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => (
              <TradeHistoryRow key={trade.id} trade={trade} onEdit={onEdit} onDelete={onDelete} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
