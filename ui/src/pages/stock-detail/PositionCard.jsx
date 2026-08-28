import { useState } from "react";
import { fmtShares, fmtPrice, fmtMoney, fmtMoneySigned, fmtPct, fmtToGo } from "../../lib/format";
import { HardCapModal } from "./HardCapModal";

function Item({ label, value, className = "" }) {
  return (
    <div>
      <div className="mb-1 text-[11px] font-semibold text-ink-muted">{label}</div>
      <div className={`num text-[15px] font-semibold ${className}`}>{value}</div>
    </div>
  );
}

/**
 * @param {{ ticker: string, position: import('../../api/types').Position }} props
 * Position grid + hard-cap progress bar, entirely server-computed
 * (profitTarget.progressDollars is already capped at targetDollars per
 * contract; remainingDollars is the authoritative "$X to go" source since
 * it isn't derivable from the capped value for losing positions). The
 * "profitTarget"/"targetDollars" wire names are the fixed contract shape;
 * "hard cap" is display wording only.
 */
export function PositionCard({ ticker, position }) {
  const [editingCap, setEditingCap] = useState(false);
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
        <div className="mb-1.5 flex items-center justify-between text-[12px]">
          <span className="text-ink-muted">Progress to hard cap</span>
          <div className="flex items-center gap-2">
            <strong className="num text-[13px] font-semibold text-ink">
              {fmtMoney(progressDollars)} of {fmtMoney(targetDollars)}
            </strong>
            <button
              type="button"
              onClick={() => setEditingCap(true)}
              className="text-[12px] font-semibold text-accent transition-colors hover:text-accent-ink hover:underline"
            >
              Edit
            </button>
          </div>
        </div>
        <div className="h-1.5 overflow-hidden rounded-pill bg-surface-sunken">
          <div
            className="h-full rounded-pill bg-good transition-[width] duration-500 ease-out"
            style={{ width: `${(progressDollars / targetDollars) * 100}%` }}
          />
        </div>
        <div className="mt-1.5 text-[12px] text-ink-muted">{fmtToGo(remainingDollars, reached)}</div>
      </div>

      <HardCapModal
        ticker={editingCap ? ticker : null}
        currentTargetDollars={targetDollars}
        onClose={() => setEditingCap(false)}
      />
    </div>
  );
}
