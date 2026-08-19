import { TrendingUp, TrendingDown } from "lucide-react";
import { SuggestionBadge } from "../../components/badge/SuggestionBadge";
import { FreshnessBar } from "../../components/layout/FreshnessBar";
import { fmtOrDash, fmtPrice, fmtPct } from "../../lib/format";

function Trend({ change1dPct }) {
  if (change1dPct == null) return <span className="text-ink-muted">{fmtOrDash(null, fmtPct)}</span>;
  const dir = change1dPct > 0.05 ? "up" : change1dPct < -0.05 ? "down" : "flat";
  const Icon = dir === "up" ? TrendingUp : dir === "down" ? TrendingDown : null;
  const colorClass = dir === "up" ? "text-good" : dir === "down" ? "text-bad" : "text-ink-muted";
  return (
    <span className={`inline-flex items-center gap-1 font-semibold ${colorClass}`}>
      {Icon && <Icon className="h-3 w-3" strokeWidth={2.5} />}
      {fmtPct(change1dPct)}
    </span>
  );
}

/**
 * @param {{
 *   ticker: string, companyName: string,
 *   currentPrice: number|null, change1dPct: number|null,
 *   badgeLabel: "BUY"|"WAIT"|"SELL"|"INSUFFICIENT",
 *   meta: import('../../api/types').Meta,
 * }} props
 * Matches the reference's `.detail-head` layout: id + price/trend on the
 * left, badge on the right border-split from the checklist (the checklist
 * itself is composed alongside this by the page, not here). Price/trend
 * render "-" via fmtOrDash when null (insufficient-history state) so the
 * row structure never jumps.
 */
export function DetailHeader({ ticker, companyName, currentPrice, change1dPct, badgeLabel, meta }) {
  return (
    <div>
      <div className="mb-0.5 flex flex-wrap items-baseline gap-2.5">
        <span className="text-[19px] font-bold tracking-tight">{ticker}</span>
        <span className="text-[13.5px] text-ink-muted">{companyName}</span>
      </div>
      <div className="my-2 flex flex-wrap items-baseline gap-3">
        <span className="num text-4xl font-semibold tracking-tight">{fmtOrDash(currentPrice, fmtPrice)}</span>
        <Trend change1dPct={change1dPct} />
      </div>
      <div className="flex flex-wrap items-center gap-2.5">
        <SuggestionBadge label={badgeLabel} size="lg" />
      </div>
      <div className="mt-3.5">
        <FreshnessBar meta={meta} showDot={false} />
      </div>
    </div>
  );
}
