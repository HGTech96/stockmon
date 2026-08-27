import { useNavigate } from "react-router-dom";
import { TriangleAlert } from "lucide-react";
import { SuggestionBadge } from "../../components/badge/SuggestionBadge";
import { Trend } from "../../components/trend/Trend";
import { fmtOrDash, fmtPct, fmtPrice, fmtRounded } from "../../lib/format";

/**
 * @param {{ result: import('../../api/types').ScreenerResult }} props
 * One clickable row -- click or Enter/Space navigates to `/screener/{ticker}`.
 * Mirrors StockRow's insufficient-history handling: price and 1-day change
 * always render (the screener's evaluation fallback still produces a real
 * price snapshot), only the indicator-derived columns dash out.
 */
export function ScreenerRow({ result }) {
  const navigate = useNavigate();
  const goToDetail = () => navigate(`/screener/${result.ticker}`);

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
        <div className="text-[13.5px] font-bold">{result.ticker}</div>
        <div className="text-[12.5px] text-ink-muted">{result.companyName}</div>
      </td>
      <td className="num px-4.5 py-3.5 text-right">{fmtPrice(result.currentPrice)}</td>
      <td className="num px-4.5 py-3.5 text-right">
        <Trend pct={result.change1dPct} />
      </td>
      <td className="num px-4.5 py-3.5 text-right">
        <Trend pct={result.change7dPct} />
      </td>
      <td className="px-4.5 py-3.5">
        {result.status === "insufficient_history" ? (
          <span className="text-[13px] text-ink-muted">Not enough data</span>
        ) : (
          <SuggestionBadge label={result.suggestion} size="sm" />
        )}
      </td>
      <td className="num px-4.5 py-3.5 text-right">
        {result.metCount == null ? <span className="text-ink-faint">–</span> : `${result.metCount} of ${result.totalCount}`}
      </td>
      <td className="num px-4.5 py-3.5 text-right">{fmtOrDash(result.rsi, fmtRounded)}</td>
      <td className="num px-4.5 py-3.5 text-right">{fmtOrDash(result.priceVs30dAvgPct, fmtPct)}</td>
      <td className="px-4.5 py-3.5 text-right">
        {result.sharpMove == null ? (
          <span className="text-ink-faint">–</span>
        ) : (
          result.sharpMove && <TriangleAlert className="ml-auto h-[15px] w-[15px] text-warn" strokeWidth={1.8} title="Sharp recent price move" />
        )}
      </td>
    </tr>
  );
}
