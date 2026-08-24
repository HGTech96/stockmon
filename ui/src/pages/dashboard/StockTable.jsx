import { SortableHeaderCell } from "../../components/table/SortableHeaderCell";
import { useTableViewState } from "../../hooks/useTableViewState";
import { StockRow } from "./StockRow";

const COLUMNS = [
  { key: "ticker", label: "Stock", align: "left", sortType: "string", accessor: (s) => s.ticker, style: { width: "26%" } },
  { key: "currentPrice", label: "Price", align: "right", sortType: "number", accessor: (s) => s.currentPrice },
  { key: "change1dPct", label: "1-day change", align: "right", sortType: "number", accessor: (s) => s.change1dPct },
  {
    key: "suggestion",
    label: "Suggestion",
    align: "left",
    sortType: "string",
    accessor: (s) => (s.status === "insufficient_history" ? null : s.suggestion),
  },
  { key: "profitLoss", label: "My P/L", align: "right", sortType: "number", accessor: (s) => s.position?.profitLoss ?? null },
];

/**
 * @param {{ stocks: import('../../api/types').DashboardStock[] }} props
 * Table shell + one <StockRow/> per entry. Row order is the server default
 * (SELL, BUY, warnings, WAIT, then insufficient-history) until the user
 * clicks a column header -- see hooks/useTableViewState.js. This component
 * still computes no values, only reorders rows the API already sent.
 */
export function StockTable({ stocks }) {
  const { rows, sort, toggleSort } = useTableViewState(stocks, COLUMNS);

  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-sunken">
              {COLUMNS.map((c) => (
                <SortableHeaderCell key={c.key} label={c.label} align={c.align} sortKey={c.key} sort={sort} onSort={toggleSort} style={c.style} />
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((stock) => (
              <StockRow key={stock.ticker} stock={stock} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
