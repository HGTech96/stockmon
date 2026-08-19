import { PositionRow } from "./PositionRow";

const HEADERS = [
  { label: "Stock", align: "left" },
  { label: "Shares", align: "right" },
  { label: "Avg cost", align: "right" },
  { label: "Invested", align: "right" },
  { label: "Current value", align: "right" },
  { label: "P/L", align: "right" },
  { label: "To target", align: "right" },
  { label: "Suggestion", align: "left" },
];

/**
 * @param {{ positions: import('../../api/types').PortfolioPosition[] }} props
 * Table shell + one <PositionRow/> per entry, in array order. Positions
 * closed by a sell (sharesHeld reduced to 0) are already excluded
 * server-side per contract -- no client filtering here.
 */
export function PositionsTable({ positions }) {
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
            {positions.map((position) => (
              <PositionRow key={position.ticker} position={position} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
