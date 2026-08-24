/**
 * Every user-facing formatter in the app lives here. Components never
 * format inline (CLAUDE.md) — the API sends raw numbers and ISO
 * timestamps/dates, this file turns them into display strings.
 */

/** @param {number} n @returns {string} "$1,234.56" (unsigned, comma grouped) */
export function fmtMoney(n) {
  return "$" + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** @param {number} n @returns {string} "+$111.20" / "-$45.00" */
export function fmtMoneySigned(n) {
  return (n >= 0 ? "+" : "-") + "$" + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * @param {number} magnitude - non-negative loss/lost figure as sent by the
 *   API (e.g. `realizedLost`, `unrealizedLossOpen` are documented as
 *   "positive number" magnitudes, not signed deltas)
 * @returns {string} "-$12.00" when > 0, "$0.00" when exactly 0 -- never a
 *   "-$0.00" or a leading "+"
 */
export function fmtLossMagnitude(magnitude) {
  return magnitude > 0 ? "-" + fmtMoney(magnitude) : fmtMoney(magnitude);
}

/**
 * @param {number} remainingDollars
 * @param {boolean} reached
 * @returns {string} "Goal reached" when reached, else "$X to go"
 */
export function fmtToGo(remainingDollars, reached) {
  return reached ? "Goal reached" : `${fmtMoney(remainingDollars)} to go`;
}

/** @param {number} n @returns {string} "+6.30%" / "-1.20%" / "0.00%" for |n| < 0.005 */
export function fmtPct(n) {
  if (Math.abs(n) < 0.005) return "0.00%";
  return (n > 0 ? "+" : "-") + Math.abs(n).toFixed(2) + "%";
}

/** @param {number} n @returns {string} "$187.42" (no comma grouping, matches design) */
export function fmtPrice(n) {
  return "$" + n.toFixed(2);
}

/** @param {number} n - raw share count @returns {string} "55.9M" */
export function fmtVolume(n) {
  return (n / 1_000_000).toFixed(1) + "M";
}

/** @param {number} n @returns {string} "1,234" or "1.25" (comma grouped, up to 6 decimals, no trailing zeros) */
export function fmtShares(n) {
  return n.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

/** @param {number} n @returns {string} nearest whole number, e.g. "55" */
export function fmtRounded(n) {
  return String(Math.round(n));
}

/** @param {string} isoDate - "YYYY-MM-DD" @returns {string} "Jul 21" */
export function fmtDateShort(isoDate) {
  return parseIsoDate(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** @param {string} isoDate - "YYYY-MM-DD" @returns {string} "Wed, Jul 21" */
export function fmtDateLong(isoDate) {
  return parseIsoDate(isoDate).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

/** @param {string} isoDatetime - ISO 8601 with timezone @returns {string} "Tuesday, 2:45 PM" */
export function fmtTimestamp(isoDatetime) {
  const d = new Date(isoDatetime);
  const weekday = d.toLocaleDateString("en-US", { weekday: "long" });
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  return `${weekday}, ${time}`;
}

/**
 * @param {string} isoDatetime - ISO 8601 with timezone
 * @returns {string} "Just now" / "5m ago" / "3h ago" / "2d ago" -- coarsest
 * whole unit, floored. Used for the screener's "Last screened" phrasing,
 * distinct from fmtTimestamp's absolute wording used for data-freshness.
 */
export function fmtRelativeTime(isoDatetime) {
  const minutes = Math.floor((Date.now() - new Date(isoDatetime).getTime()) / 60_000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/**
 * @param {*} value
 * @param {(value: *) => string} formatter
 * @returns {string} "–" when value is null/undefined, else formatter(value).
 * The one place the null-numeric-to-dash convention lives, so every
 * nullable contract field renders the same character the same way.
 */
export function fmtOrDash(value, formatter) {
  return value == null ? "–" : formatter(value);
}

/**
 * @param {import('../api/types').RefreshResponse} refreshResult
 * @returns {string|null} "5 updated · AMZN, KO failed" -- null when nothing
 * failed. Names the failed tickers rather than just a count, so a stale
 * price is identifiable at a glance instead of forcing a hunt through the
 * table.
 */
export function fmtRefreshSummary(refreshResult) {
  if (refreshResult.failed.length === 0) return null;
  const failedTickers = refreshResult.failed.map((f) => f.ticker).join(", ");
  return `${refreshResult.refreshed.length} updated · ${failedTickers} failed`;
}

/** @param {string} isoDate - "YYYY-MM-DD", parsed as local (not UTC midnight) so chart labels don't shift a day off */
function parseIsoDate(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day);
}
