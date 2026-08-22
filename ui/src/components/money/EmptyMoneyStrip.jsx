import { Button } from "../ui/button";
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
    <Button variant="outline" size="icon-sm" aria-label="Deposit" className="text-base leading-none font-bold" onClick={onDeposit}>
      +
    </Button>
  );

  return (
    <div className="mb-6 overflow-hidden rounded-DEFAULT border border-border sm:w-1/3">
      <MoneyCluster label="Cash" actions={depositAction}>
        <MoneyTile label="Cash available" value={fmtMoney(0)} />
      </MoneyCluster>
    </div>
  );
}
