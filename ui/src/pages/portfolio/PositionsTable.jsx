import { SortableHeaderCell } from "../../components/table/SortableHeaderCell";
import { useTableViewState } from "../../hooks/useTableViewState";
import { PositionRow } from "./PositionRow";

const COLUMNS = [
  { key: "ticker", label: "Stock", align: "left", sortType: "string", accessor: (p) => p.ticker },
  { key: "sharesHeld", label: "Shares", align: "right", sortType: "number", accessor: (p) => p.sharesHeld },
  { key: "avgPurchasePrice", label: "Avg cost", align: "right", sortType: "number", accessor: (p) => p.avgPurchasePrice },
  { key: "amountInvested", label: "Invested", align: "right", sortType: "number", accessor: (p) => p.amountInvested },
  { key: "currentValue", label: "Current value", align: "right", sortType: "number", accessor: (p) => p.currentValue },
  { key: "profitLoss", label: "P/L", align: "right", sortType: "number", accessor: (p) => p.profitLoss },
  { key: "remainingDollars", label: "To target", align: "right", sortType: "number", accessor: (p) => p.profitTarget.remainingDollars },
  {
    key: "suggestion",
    label: "Suggestion",
    align: "left",
    sortType: "string",
    accessor: (p) => (p.status === "insufficient_history" ? null : p.suggestion),
  },
];

/**
 * @param {{ positions: import('../../api/types').PortfolioPosition[] }} props
 * Table shell + one <PositionRow/> per entry. Row order is the server
 * default until the user clicks a column header -- see
 * hooks/useTableViewState.js. Positions closed by a sell (sharesHeld
 * reduced to 0) are already excluded server-side per contract -- no
 * client filtering here.
 */
export function PositionsTable({ positions }) {
  const { rows, sort, toggleSort } = useTableViewState(positions, COLUMNS);

  return (
    <div className="overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-sunken">
              {COLUMNS.map((c) => (
                <SortableHeaderCell key={c.key} label={c.label} align={c.align} sortKey={c.key} sort={sort} onSort={toggleSort} />
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((position) => (
              <PositionRow key={position.ticker} position={position} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
