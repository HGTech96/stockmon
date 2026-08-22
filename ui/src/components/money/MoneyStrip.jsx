import { Button } from "../ui/button";
import { fmtMoney, fmtMoneySigned, fmtLossMagnitude } from "../../lib/format";
import { MoneyCluster } from "./MoneyCluster";
import { MoneyTile } from "./MoneyTile";

/**
 * @param {{ money: import('../../api/types').Money, onDeposit: () => void, onWithdraw: () => void }} props
 * Second summary strip, mounted below the existing 3-card SummaryStrip:
 * Cash | Realized | Unrealized clusters for the six money-block figures
 * (contract v1.5). The Unrealized cluster's tiles are tinted (`live`) --
 * confirmed in the phase 9b design review over dot+caption alone.
 */
export function MoneyStrip({ money, onDeposit, onWithdraw }) {
  const depositWithdrawActions = (
    <div className="flex gap-1.5">
      <Button variant="outline" size="icon-sm" aria-label="Deposit" className="text-base leading-none font-bold" onClick={onDeposit}>
        +
      </Button>
      <Button variant="outline" size="icon-sm" aria-label="Withdraw" className="text-base leading-none font-bold" onClick={onWithdraw}>
        −
      </Button>
    </div>
  );

  return (
    <div className="mb-6 grid grid-cols-1 gap-px overflow-hidden rounded-DEFAULT border border-border bg-border sm:grid-cols-3">
      <MoneyCluster label="Cash" actions={depositWithdrawActions}>
        <MoneyTile label="Cash available" value={fmtMoney(money.cashAvailable)} />
        <MoneyTile label="Net deposited" value={fmtMoney(money.netDeposited)} sub="real money put in" />
      </MoneyCluster>

      <MoneyCluster label="Realized (banked)">
        <MoneyTile
          label="Earned"
          value={fmtMoneySigned(money.realizedEarned)}
          tone={money.realizedEarned > 0 ? "good" : "neutral"}
        />
        <MoneyTile
          label="Lost"
          value={fmtLossMagnitude(money.realizedLost)}
          tone={money.realizedLost > 0 ? "bad" : "neutral"}
        />
      </MoneyCluster>

      <MoneyCluster label="Unrealized (open)" live>
        <MoneyTile
          label="Gain"
          value={fmtMoneySigned(money.unrealizedGainOpen)}
          tone={money.unrealizedGainOpen > 0 ? "good" : "neutral"}
          live
        />
        <MoneyTile
          label="Loss"
          value={fmtLossMagnitude(money.unrealizedLossOpen)}
          tone={money.unrealizedLossOpen > 0 ? "bad" : "neutral"}
          live
        />
      </MoneyCluster>
    </div>
  );
}
