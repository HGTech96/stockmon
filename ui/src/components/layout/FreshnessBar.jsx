/**
 * Minimal placeholder formatter -- real "Tuesday, 2:45 PM" formatting
 * lives in lib/format.js once that's built out in Phase 5. This keeps
 * the raw ISO timestamp readable without inlining formatting logic in JSX.
 * @param {string} isoTimestamp
 */
function formatTimestampPlaceholder(isoTimestamp) {
  return new Date(isoTimestamp).toLocaleString();
}

/**
 * The compact "dot + Data as of ..." indicator that sits in the app bar.
 * The full-width stale banner is a separate element (AppShell renders it
 * directly below the header), matching the reference design's split
 * between `.freshness` and `.global-banner`.
 * @param {{ meta: import('../../api/types').Meta | undefined }} props
 */
export function FreshnessBar({ meta }) {
  if (!meta) return null;

  return (
    <div className="flex items-center gap-2 whitespace-nowrap text-xs text-ink-muted">
      <span
        className={`h-[7px] w-[7px] flex-none rounded-full ${
          meta.isStale ? "bg-warn" : "bg-good"
        }`}
      />
      <span>Data as of {formatTimestampPlaceholder(meta.dataAsOf)}</span>
    </div>
  );
}
