import { fmtShares, fmtPrice, fmtMoney, fmtMoneySigned, fmtPct } from "../../lib/format";

function Item({ label, value, className = "" }) {
  return (
    <div>
      <div className="mb-1 text-[11.5px] font-semibold text-ink-muted">{label}</div>
      <div className={`num text-[15px] font-semibold ${className}`}>{value}</div>
    </div>
  );
}

/**
 * @param {{ position: import('../../api/types').Position }} props
 * Position grid + profit-target progress bar, entirely server-computed
 * (profitTarget.progressDollars is already capped at targetDollars per
 * contract; remainingDollars is the authoritative "$X to go" source since
 * it isn't derivable from the capped value for losing positions).
 */
export function PositionCard({ position }) {
  const plClass = position.profitLoss >= 0 ? "text-good" : "text-bad";
  const { targetDollars, progressDollars, remainingDollars, reached } = position.profitTarget;

  return (
    <div>
      <div className="mb-4 grid grid-cols-2 gap-x-5 gap-y-3">
        <Item label="Shares held" value={fmtShares(position.sharesHeld)} />
        <Item label="Average purchase price" value={fmtPrice(position.avgPurchasePrice)} />
        <Item label="Amount invested" value={fmtMoney(position.amountInvested)} />
        <Item label="Current value" value={fmtMoney(position.currentValue)} />
        <Item label="Profit / loss" value={fmtMoneySigned(position.profitLoss)} className={plClass} />
        <Item label="Profit / loss %" value={fmtPct(position.profitLossPct)} className={plClass} />
      </div>
      <div className="border-t border-border pt-3.5">
        <div className="mb-1.5 flex justify-between text-[12.5px]">
          <span>Progress to profit target</span>
          <strong className="num text-[13px] font-semibold text-ink">
            {fmtMoney(progressDollars)} of {fmtMoney(targetDollars)}
          </strong>
        </div>
        <div className="h-2 overflow-hidden rounded-pill bg-surface-sunken">
          <div className="h-full rounded-pill bg-good" style={{ width: `${(progressDollars / targetDollars) * 100}%` }} />
        </div>
        <div className="mt-1.5 text-[12px] text-ink-muted">{reached ? "Goal reached" : `${fmtMoney(remainingDollars)} to go`}</div>
      </div>
    </div>
  );
}
