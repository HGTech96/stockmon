import { TrendingUp, TrendingDown } from "lucide-react";
import { fmtOrDash, fmtPct } from "../../lib/format";

/**
 * @param {{ pct: number|null }} props
 * Arrow + colored percent-change text: green/up when > 0.05, red/down when
 * < -0.05, gray/flat (no icon) otherwise; renders "–" via fmtOrDash when
 * null. Shared by the detail-page header, dashboard table rows, and the
 * screener's 1-day/7-day change columns so they all use identical
 * direction/color logic.
 */
export function Trend({ pct }) {
  if (pct == null) return <span className="text-ink-muted">{fmtOrDash(null, fmtPct)}</span>;

  const dir = pct > 0.05 ? "up" : pct < -0.05 ? "down" : "flat";
  const Icon = dir === "up" ? TrendingUp : dir === "down" ? TrendingDown : null;
  const colorClass = dir === "up" ? "text-good" : dir === "down" ? "text-bad" : "text-ink-muted";

  return (
    <span className={`inline-flex items-center gap-1 font-semibold ${colorClass}`}>
      {Icon && <Icon className="h-3 w-3" strokeWidth={2.5} />}
      {fmtPct(pct)}
    </span>
  );
}
