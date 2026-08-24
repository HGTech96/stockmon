import { NoFilterResults } from "../../components/table/NoFilterResults";
import { SortableHeaderCell } from "../../components/table/SortableHeaderCell";
import { TableFilterBar } from "../../components/table/TableFilterBar";
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

const FILTER_CONFIG = {
  searchText: (s) => `${s.ticker} ${s.companyName}`,
  suggestion: (s) => (s.status === "insufficient_history" ? "INSUFFICIENT" : s.suggestion),
  owned: (s) => s.position != null,
};

/**
 * @param {{ stocks: import('../../api/types').DashboardStock[] }} props
 * Table shell + one <StockRow/> per entry. Row order is the server default
 * (SELL, BUY, warnings, WAIT, then insufficient-history) until the user
 * clicks a column header, and the row set is the full watchlist until the
 * user searches/filters -- see hooks/useTableViewState.js. This component
 * still computes no values, only reorders/narrows rows the API already sent.
 */
export function StockTable({ stocks }) {
  const { rows, sort, toggleSort, filters, setSearch, toggleSuggestion, setOwned, resetFilters, isFiltered } = useTableViewState(
    stocks,
    COLUMNS,
    FILTER_CONFIG,
  );

  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <TableFilterBar
        filters={filters}
        onSearch={setSearch}
        onToggleSuggestion={toggleSuggestion}
        onOwnedChange={setOwned}
        onReset={resetFilters}
        showOwnedToggle
        isFiltered={isFiltered}
      />
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
            {rows.length === 0 && isFiltered ? (
              <NoFilterResults colSpan={COLUMNS.length} onReset={resetFilters} />
            ) : (
              rows.map((stock) => <StockRow key={stock.ticker} stock={stock} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
