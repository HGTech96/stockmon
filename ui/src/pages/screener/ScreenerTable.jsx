import { motion } from "motion/react";
import { NoFilterResults } from "../../components/table/NoFilterResults";
import { SortableHeaderCell } from "../../components/table/SortableHeaderCell";
import { TableFilterBar } from "../../components/table/TableFilterBar";
import { useTableViewState } from "../../hooks/useTableViewState";
import { ScreenerRow } from "./ScreenerRow";

const listVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.035 } },
};

const COLUMNS = [
  { key: "ticker", label: "Stock", align: "left", sortType: "string", accessor: (r) => r.ticker, style: { width: "22%" } },
  { key: "currentPrice", label: "Price", align: "right", sortType: "number", accessor: (r) => r.currentPrice },
  { key: "change1dPct", label: "1-day change", align: "right", sortType: "number", accessor: (r) => r.change1dPct },
  { key: "change7dPct", label: "7-day change", align: "right", sortType: "number", accessor: (r) => r.change7dPct },
  {
    key: "suggestion",
    label: "Suggestion",
    align: "left",
    sortType: "string",
    accessor: (r) => (r.status === "insufficient_history" ? null : r.suggestion),
  },
  { key: "metCount", label: "Conditions met", align: "right", sortType: "number", accessor: (r) => r.metCount },
  { key: "rsi", label: "RSI", align: "right", sortType: "number", accessor: (r) => r.rsi },
  { key: "priceVs30dAvgPct", label: "vs 30d avg", align: "right", sortType: "number", accessor: (r) => r.priceVs30dAvgPct },
  { key: "sharpMove", label: "Move", align: "right", sortType: "number", accessor: (r) => (r.sharpMove == null ? null : Number(r.sharpMove)) },
];

const FILTER_CONFIG = {
  searchText: (r) => `${r.ticker} ${r.companyName}`,
  suggestion: (r) => (r.status === "insufficient_history" ? "INSUFFICIENT" : r.suggestion),
  // no `owned` key -- screener stocks are never owned, no owned/not-owned toggle
};

/**
 * @param {{ results: import('../../api/types').ScreenerResult[], viewState?: {sort, setSort, filters, setFilters} }} props
 * Table shell + one <ScreenerRow/> per entry. Reuses the exact Phase 12/13
 * view-state layer StockTable/PositionsTable already use -- this component
 * still computes nothing, only reorders/narrows rows the API already sent.
 * `viewState` (from ScreenerSection, Phase 17) lifts sort/filter state above
 * this component so it survives navigating to a row's detail page and back.
 */
export function ScreenerTable({ results, viewState }) {
  const { rows, sort, toggleSort, filters, setSearch, toggleSuggestion, resetFilters, isFiltered } = useTableViewState(
    results,
    COLUMNS,
    FILTER_CONFIG,
    viewState,
  );

  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <TableFilterBar filters={filters} onSearch={setSearch} onToggleSuggestion={toggleSuggestion} onReset={resetFilters} isFiltered={isFiltered} />
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-sunken">
              {COLUMNS.map((c) => (
                <SortableHeaderCell key={c.key} label={c.label} align={c.align} sortKey={c.key} sort={sort} onSort={toggleSort} style={c.style} />
              ))}
            </tr>
          </thead>
          <motion.tbody
            key={filters.search + [...filters.suggestions].join(",")}
            variants={listVariants}
            initial="hidden"
            animate="visible"
          >
            {rows.length === 0 && isFiltered ? (
              <NoFilterResults colSpan={COLUMNS.length} onReset={resetFilters} />
            ) : (
              rows.map((result) => <ScreenerRow key={result.ticker} result={result} />)
            )}
          </motion.tbody>
        </table>
      </div>
    </div>
  );
}
