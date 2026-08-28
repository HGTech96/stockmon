import { useNavigate } from "react-router-dom";
import { motion } from "motion/react";
import { SuggestionBadge } from "../../components/badge/SuggestionBadge";
import { fmtShares, fmtPrice, fmtMoney, fmtMoneySigned, fmtPct, fmtToGo } from "../../lib/format";

const rowVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0 },
};

/**
 * @param {{ position: import('../../api/types').PortfolioPosition }} props
 * One clickable row -- click or Enter/Space navigates to `/stocks/{ticker}`,
 * same pattern as Dashboard's StockRow. Suggestion column: badge for "ok"
 * rows, plain muted "Not enough data" text for insufficient-history rows --
 * same convention 5b established for Dashboard.
 */
export function PositionRow({ position }) {
  const navigate = useNavigate();
  const goToDetail = () => navigate(`/stocks/${position.ticker}`);
  const plClass = position.profitLoss >= 0 ? "text-good" : "text-bad";
  const { remainingDollars, reached } = position.profitTarget;

  return (
    <motion.tr
      variants={rowVariants}
      className="cursor-pointer border-b border-border last:border-b-0 hover:bg-surface-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
      tabIndex={0}
      onClick={goToDetail}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          goToDetail();
        }
      }}
    >
      <td className="px-4.5 py-3.5">
        <div className="text-[13.5px] font-bold">{position.ticker}</div>
        <div className="text-[12px] text-ink-muted">{position.companyName}</div>
      </td>
      <td className="num px-4.5 py-3.5 text-right">{fmtShares(position.sharesHeld)}</td>
      <td className="num px-4.5 py-3.5 text-right">{fmtPrice(position.avgPurchasePrice)}</td>
      <td className="num px-4.5 py-3.5 text-right">{fmtMoney(position.amountInvested)}</td>
      <td className="num px-4.5 py-3.5 text-right">{fmtMoney(position.currentValue)}</td>
      <td className="num px-4.5 py-3.5 text-right">
        <span className={plClass}>
          {fmtMoneySigned(position.profitLoss)} <span className="text-ink-faint">({fmtPct(position.profitLossPct)})</span>
        </span>
      </td>
      <td className="num px-4.5 py-3.5 text-right">{fmtToGo(remainingDollars, reached)}</td>
      <td className="px-4.5 py-3.5">
        {position.status === "insufficient_history" ? (
          <span className="text-[13px] text-ink-muted">Not enough data</span>
        ) : (
          <SuggestionBadge label={position.suggestion} size="sm" />
        )}
      </td>
    </motion.tr>
  );
}
