import { motion } from "motion/react";
import { NoFilterResults } from "../../components/table/NoFilterResults";
import { SortableHeaderCell } from "../../components/table/SortableHeaderCell";
import { TableFilterBar } from "../../components/table/TableFilterBar";
import { useTableViewState } from "../../hooks/useTableViewState";
import { PositionRow } from "./PositionRow";

const listVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.035 } },
};

const COLUMNS = [
  { key: "ticker", label: "Stock", align: "left", sortType: "string", accessor: (p) => p.ticker },
  { key: "sharesHeld", label: "Shares", align: "right", sortType: "number", accessor: (p) => p.sharesHeld },
  { key: "avgPurchasePrice", label: "Avg cost", align: "right", sortType: "number", accessor: (p) => p.avgPurchasePrice },
  { key: "amountInvested", label: "Invested", align: "right", sortType: "number", accessor: (p) => p.amountInvested },
  { key: "currentValue", label: "Current value", align: "right", sortType: "number", accessor: (p) => p.currentValue },
  { key: "profitLoss", label: "P/L", align: "right", sortType: "number", accessor: (p) => p.profitLoss },
  { key: "remainingDollars", label: "To cap", align: "right", sortType: "number", accessor: (p) => p.profitTarget.remainingDollars },
  {
    key: "suggestion",
    label: "Suggestion",
    align: "left",
    sortType: "string",
    accessor: (p) => (p.status === "insufficient_history" ? null : p.suggestion),
  },
];

const FILTER_CONFIG = {
  searchText: (p) => `${p.ticker} ${p.companyName}`,
  suggestion: (p) => (p.status === "insufficient_history" ? "INSUFFICIENT" : p.suggestion),
};

/**
 * @param {{ positions: import('../../api/types').PortfolioPosition[] }} props
 * Table shell + one <PositionRow/> per entry. Row order is the server
 * default until the user clicks a column header, and the row set is every
 * open position until the user searches/filters -- see
 * hooks/useTableViewState.js. Positions closed by a sell (sharesHeld
 * reduced to 0) are already excluded server-side per contract -- no owned
 * toggle here, every row is already owned.
 */
export function PositionsTable({ positions }) {
  const { rows, sort, toggleSort, filters, setSearch, toggleSuggestion, resetFilters, isFiltered } = useTableViewState(
    positions,
    COLUMNS,
    FILTER_CONFIG,
  );

  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <TableFilterBar filters={filters} onSearch={setSearch} onToggleSuggestion={toggleSuggestion} onReset={resetFilters} isFiltered={isFiltered} />
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-sunken">
              {COLUMNS.map((c) => (
                <SortableHeaderCell key={c.key} label={c.label} align={c.align} sortKey={c.key} sort={sort} onSort={toggleSort} />
              ))}
            </tr>
          </thead>
          <motion.tbody key={filters.search + [...filters.suggestions].join(",")} variants={listVariants} initial="hidden" animate="visible">
            {rows.length === 0 && isFiltered ? (
              <NoFilterResults colSpan={COLUMNS.length} onReset={resetFilters} />
            ) : (
              rows.map((position) => <PositionRow key={position.ticker} position={position} />)
            )}
          </motion.tbody>
        </table>
      </div>
    </div>
  );
}
