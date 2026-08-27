import { useNavigate } from "react-router-dom";
import { TriangleAlert } from "lucide-react";
import { SuggestionBadge } from "../../components/badge/SuggestionBadge";
import { Trend } from "../../components/trend/Trend";
import { fmtPrice, fmtMoneySigned, fmtPct } from "../../lib/format";

/**
 * @param {{ stock: import('../../api/types').DashboardStock }} props
 * One clickable row -- click or Enter/Space navigates to `/stocks/{ticker}`.
 * Price and 1-day change always render the real values the API sent, even
 * for `insufficient_history` rows (the contract sends real numbers there --
 * a stock has a real price and daily change regardless of history length).
 * Suggestion column is the badge for "ok" rows, or plain muted "Not enough
 * data" text (not badge chrome) for insufficient-history rows. P/L dashes
 * when `position` is null.
 */
export function StockRow({ stock }) {
  const navigate = useNavigate();
  const goToDetail = () => navigate(`/stocks/${stock.ticker}`);

  return (
    <tr
      className="cursor-pointer border-b border-border last:border-b-0 hover:bg-surface-sunken focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
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
        <div className="flex items-center gap-2.5">
          {stock.warning && (
            <TriangleAlert className="h-[15px] w-[15px] flex-none text-warn" strokeWidth={1.8} title="Sharp recent price move, check news" />
          )}
          <div>
            <div className="text-[13.5px] font-bold">{stock.ticker}</div>
            <div className="text-[12.5px] text-ink-muted">{stock.companyName}</div>
          </div>
        </div>
      </td>
      <td className="num px-4.5 py-3.5 text-right">{fmtPrice(stock.currentPrice)}</td>
      <td className="num px-4.5 py-3.5 text-right">
        <Trend pct={stock.change1dPct} />
      </td>
      <td className="px-4.5 py-3.5">
        {stock.status === "insufficient_history" ? (
          <span className="text-[13px] text-ink-muted">Not enough data</span>
        ) : (
          <SuggestionBadge label={stock.suggestion} size="sm" />
        )}
      </td>
      <td className="num px-4.5 py-3.5 text-right">
        {stock.position ? (
          <span className={stock.position.profitLoss >= 0 ? "text-good" : "text-bad"}>
            {fmtMoneySigned(stock.position.profitLoss)} <span className="text-ink-faint">({fmtPct(stock.position.profitLossPct)})</span>
          </span>
        ) : (
          <span className="text-ink-faint">–</span>
        )}
      </td>
    </tr>
  );
}
