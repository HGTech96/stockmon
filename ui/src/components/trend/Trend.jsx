import { TrendingUp, TrendingDown } from "lucide-react";
import { fmtOrDash, fmtPct } from "../../lib/format";

/**
 * @param {{ change1dPct: number|null }} props
 * Arrow + colored 1-day-change text: green/up when > 0.05, red/down when
 * < -0.05, gray/flat (no icon) otherwise; renders "–" via fmtOrDash when
 * null. Shared by the detail-page header and dashboard table rows so both
 * use identical direction/color logic.
 */
export function Trend({ change1dPct }) {
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
