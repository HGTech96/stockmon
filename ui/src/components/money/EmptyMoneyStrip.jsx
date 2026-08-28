import { fmtMoney } from "../../lib/format";
import { MoneyCluster } from "./MoneyCluster";
import { MoneyTile } from "./MoneyTile";

/**
 * @param {{ onDeposit: () => void }} props
 * Rendered instead of MoneyStrip when `money` is null -- a fresh DB with
 * no cash activity and no trades yet. Without this, there would be no
 * Deposit entry point anywhere in the UI (MoneyStrip itself only exists
 * once `money` is non-null), leaving a brand-new install with no way to
 * make its first deposit except by calling the API directly. Single Cash
 * cluster, no Withdraw (nothing to withdraw before a first deposit).
 */
export function EmptyMoneyStrip({ onDeposit }) {
  const depositAction = (
    <button
      type="button"
      aria-label="Deposit"
      onClick={onDeposit}
      className="flex h-7 w-7 items-center justify-center rounded-sm border border-good-border bg-good-bg text-base leading-none font-bold text-good transition-colors hover:bg-good hover:text-white active:translate-y-px"
    >
      +
    </button>
  );

  return (
    <div className="mb-6 overflow-hidden rounded-DEFAULT border border-border sm:w-1/3">
      <MoneyCluster label="Cash" actions={depositAction}>
        <MoneyTile label="Cash available" value={fmtMoney(0)} />
      </MoneyCluster>
    </div>
  );
}
