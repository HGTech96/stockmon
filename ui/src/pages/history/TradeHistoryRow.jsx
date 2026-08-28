import { motion } from "motion/react";
import { Pencil, Trash2 } from "lucide-react";
import { ActionBadge } from "../../components/badge/ActionBadge";
import { fmtDateShort, fmtShares, fmtPrice, fmtMoney, fmtMoneySigned } from "../../lib/format";

const rowVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0 },
};

/**
 * @param {{
 *   trade: import('../../api/types').TradeHistoryEntry,
 *   onEdit: (trade: import('../../api/types').TradeHistoryEntry) => void,
 *   onDelete: (trade: import('../../api/types').TradeHistoryEntry) => void,
 * }} props
 * Row itself isn't clickable -- trades have no detail page. realizedPnlUsd
 * is null on buys (dash), colored green/red on sells per the fixed P/L
 * color rule. Edit/delete icon buttons open the respective dialogs.
 */
export function TradeHistoryRow({ trade, onEdit, onDelete }) {
  return (
    <motion.tr variants={rowVariants} className="border-b border-border last:border-b-0">
      <td className="px-4.5 py-3.5 text-[13.5px] text-ink-muted">{fmtDateShort(trade.date)}</td>
      <td className="px-4.5 py-3.5">
        <div className="text-[13.5px] font-bold">{trade.ticker}</div>
        <div className="text-[12px] text-ink-muted">{trade.companyName}</div>
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
      <td className="px-4.5 py-3.5">
        <div className="flex items-center justify-end gap-1">
          <button
            type="button"
            onClick={() => onEdit(trade)}
            aria-label={`Edit ${trade.ticker} trade`}
            className="rounded-sm p-1.5 text-ink-muted transition-colors hover:bg-surface-hover hover:text-ink active:translate-y-px"
          >
            <Pencil className="h-3.5 w-3.5" strokeWidth={1.6} />
          </button>
          <button
            type="button"
            onClick={() => onDelete(trade)}
            aria-label={`Delete ${trade.ticker} trade`}
            className="rounded-sm p-1.5 text-ink-muted transition-colors hover:bg-bad-bg hover:text-bad active:translate-y-px"
          >
            <Trash2 className="h-3.5 w-3.5" strokeWidth={1.6} />
          </button>
        </div>
      </td>
    </motion.tr>
  );
}
