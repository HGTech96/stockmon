import { Clock } from "lucide-react";

/**
 * @param {{
 *   daysOfHistoryAvailable: number,
 *   daysOfHistoryRequired: number,
 *   tradingDaysUntilReady: number|null,
 * }} props
 */
export function InsufficientHistoryPanel({ daysOfHistoryAvailable, daysOfHistoryRequired, tradingDaysUntilReady }) {
  return (
    <div>
      <div className="mb-2.5 text-xs font-bold tracking-wide text-ink-muted uppercase">Why</div>
      <div className="flex items-center gap-3.5 rounded-lg border border-dashed border-border-strong bg-surface-sunken px-4.5 py-4">
        <Clock className="h-[22px] w-[22px] flex-none text-ink-faint" strokeWidth={1.5} />
        <div>
          <div className="mb-0.5 text-[13.5px] font-bold">Not enough data yet</div>
          <div className="text-[12.5px] text-ink-muted">
            Needs {daysOfHistoryRequired} days of price history to generate a suggestion. Currently tracking{" "}
            {daysOfHistoryAvailable} of {daysOfHistoryRequired} days
            {tradingDaysUntilReady != null && `, check back in ${tradingDaysUntilReady} more trading days`}.
          </div>
        </div>
      </div>
    </div>
  );
}
