import { fmtMoney, fmtMoneySigned, fmtPct } from "../../lib/format";

function Tile({ label, value, sub, className = "" }) {
  return (
    <div className="bg-surface px-5 py-4">
      <div className="mb-1.5 text-[11px] font-semibold tracking-wide text-ink-muted uppercase">{label}</div>
      <div className={`num text-[22px] font-semibold tracking-tight ${className}`}>{value}</div>
      {sub && <div className={`num mt-0.5 text-[12.5px] ${className}`}>{sub}</div>}
    </div>
  );
}

/**
 * @param {{ summary: import('../../api/types').Summary }} props
 * Three tiles: Total invested, Total current value, Total profit/loss (with
 * its % as a colored sub-line). Caller decides whether to render this at
 * all -- both `GET /api/stocks` and `GET /api/portfolio` send
 * `summary: null` when no trades are recorded; this component doesn't
 * special-case that, it just isn't mounted in that state.
 */
export function SummaryStrip({ summary }) {
  const plClass = summary.totalProfitLoss >= 0 ? "text-good" : "text-bad";

  return (
    <div className="mb-6 grid grid-cols-1 gap-px overflow-hidden rounded-DEFAULT border border-border bg-border sm:grid-cols-3">
      <Tile label="Total invested" value={fmtMoney(summary.totalInvested)} />
      <Tile label="Total current value" value={fmtMoney(summary.totalCurrentValue)} />
      <Tile
        label="Total profit / loss"
        value={fmtMoneySigned(summary.totalProfitLoss)}
        sub={fmtPct(summary.totalProfitLossPct)}
        className={plClass}
      />
    </div>
  );
}
