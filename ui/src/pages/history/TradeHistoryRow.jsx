import { ActionBadge } from "../../components/badge/ActionBadge";
import { fmtDateShort, fmtShares, fmtPrice, fmtMoney, fmtMoneySigned } from "../../lib/format";

/**
 * @param {{ trade: import('../../api/types').TradeHistoryEntry }} props
 * Not clickable -- trades have no detail page. realizedPnlUsd is null on
 * buys (dash), colored green/red on sells per the fixed P/L color rule.
 */
export function TradeHistoryRow({ trade }) {
  return (
    <tr className="border-b border-border last:border-b-0">
      <td className="px-4.5 py-3.5 text-[13.5px] text-ink-muted">{fmtDateShort(trade.date)}</td>
      <td className="px-4.5 py-3.5">
        <div className="text-[13.5px] font-bold">{trade.ticker}</div>
        <div className="text-[12.5px] text-ink-muted">{trade.companyName}</div>
      </td>
      <td className="px-4.5 py-3.5">
        <ActionBadge action={trade.action} />
      </td>
      <td className="num px-4.5 py-3.5 text-right">{fmtShares(trade.shares)}</td>
      <td className="num px-4.5 py-3.5 text-right">{fmtPrice(trade.pricePerShare)}</td>
      <td className="num px-4.5 py-3.5 text-right">{fmtMoney(trade.totalUsd)}</td>
      <td className="num px-4.5 py-3.5 text-right">
        {trade.realizedPnlUsd == null ? (
          <span className="text-ink-faint">–</span>
        ) : (
          <span className={trade.realizedPnlUsd >= 0 ? "text-good" : "text-bad"}>
            {fmtMoneySigned(trade.realizedPnlUsd)}
          </span>
        )}
      </td>
    </tr>
  );
}
