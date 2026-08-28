/**
 * "Market Open" / "Pre-Market Open" / "After Hours" / "Market Closed" dot +
 * text, sourced from meta.marketStatus/marketStatusText -- backend-owned
 * wording, this component only maps the machine enum to a dot color.
 * @param {{
 *   marketStatus: import('../../api/types').Meta['marketStatus'] | undefined,
 *   marketStatusText: string | undefined,
 *   showDot?: boolean,
 * }} props
 */
export function MarketStatusBadge({ marketStatus, marketStatusText, showDot = true }) {
  if (!marketStatus) return null;

  return (
    <div className="flex items-center gap-2 whitespace-nowrap text-xs text-ink-muted">
      {showDot && (
        <span
          className={`h-[7px] w-[7px] flex-none rounded-full ${
            marketStatus === "open" ? "bg-good" : "bg-neutral"
          }`}
        />
      )}
      <span>{marketStatusText}</span>
    </div>
  );
}
