import { fmtTimestamp } from "../../lib/format";

/**
 * "Data as of ..." freshness text, with an optional leading status dot.
 * One component, two placements: `AppShell` renders it with the dot
 * (compact app-bar indicator), `DetailHeader` renders it dot-less as the
 * per-page timestamp line -- so a screenshot of a single page still
 * carries its own data-freshness timestamp, matching the reference's
 * separate `.freshness` (app bar) and `.detail-head__timestamp` elements.
 * The full-width stale banner is a separate element AppShell renders
 * directly below the header.
 * @param {{ meta: import('../../api/types').Meta | undefined, showDot?: boolean }} props
 */
export function FreshnessBar({ meta, showDot = true }) {
  if (!meta) return null;

  return (
    <div className="flex items-center gap-2 whitespace-nowrap text-xs text-ink-muted">
      {showDot && (
        <span
          className={`h-[7px] w-[7px] flex-none rounded-full ${
            meta.isStale ? "bg-warn" : "bg-good"
          }`}
        />
      )}
      <span>Data as of {fmtTimestamp(meta.dataAsOf)}</span>
    </div>
  );
}
