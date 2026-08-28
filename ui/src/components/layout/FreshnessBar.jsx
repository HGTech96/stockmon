import { fmtTimestamp } from "../../lib/format";
import { MarketStatusBadge } from "./MarketStatusBadge";
import { LiveDot } from "./LiveDot";

/**
 * "Data as of ..." freshness text plus the market-status badge, with an
 * optional leading status dot on each. One component, two placements:
 * `AppShell` renders it with the dot (compact app-bar indicator),
 * `DetailHeader` renders it dot-less as the per-page timestamp line -- so a
 * screenshot of a single page still carries its own data-freshness
 * timestamp, matching the reference's separate `.freshness` (app bar) and
 * `.detail-head__timestamp` elements. The full-width stale banner is a
 * separate element AppShell renders directly below the header.
 * @param {{ meta: import('../../api/types').Meta | undefined, showDot?: boolean }} props
 */
export function FreshnessBar({ meta, showDot = true }) {
  if (!meta) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 whitespace-nowrap text-xs text-ink-muted">
      <div className="flex items-center gap-2">
        {showDot && <LiveDot tone={meta.isStale ? "warn" : "good"} />}
        <span>Data as of {fmtTimestamp(meta.dataAsOf)}</span>
      </div>
      <span aria-hidden="true">&middot;</span>
      <MarketStatusBadge
        marketStatus={meta.marketStatus}
        marketStatusText={meta.marketStatusText}
        showDot={showDot}
      />
    </div>
  );
}
