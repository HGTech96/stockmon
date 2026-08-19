import { StockRow } from "./StockRow";

/**
 * @param {{ stocks: import('../../api/types').DashboardStock[] }} props
 * Table shell + one <StockRow/> per entry, rendered in exactly the order
 * the array arrives in. The contract guarantees server-side ordering
 * (SELL, BUY, warnings, WAIT, then insufficient-history) -- this component
 * does not sort, filter, or re-rank.
 */
export function StockTable({ stocks }) {
  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-sunken">
              <th className="px-4.5 py-2.5 text-left text-[11.5px] font-bold tracking-wide text-ink-muted uppercase" style={{ width: "26%" }}>
                Stock
              </th>
              <th className="px-4.5 py-2.5 text-right text-[11.5px] font-bold tracking-wide text-ink-muted uppercase">Price</th>
              <th className="px-4.5 py-2.5 text-right text-[11.5px] font-bold tracking-wide text-ink-muted uppercase">1-day change</th>
              <th className="px-4.5 py-2.5 text-left text-[11.5px] font-bold tracking-wide text-ink-muted uppercase">Suggestion</th>
              <th className="px-4.5 py-2.5 text-right text-[11.5px] font-bold tracking-wide text-ink-muted uppercase">My P/L</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <StockRow key={stock.ticker} stock={stock} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
