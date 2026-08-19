import { TriangleAlert } from "lucide-react";

/**
 * @param {{ warning: import('../../api/types').Warning|null }} props
 * Renders `warning.text` verbatim -- no client-composed second sentence
 * from ticker/change1dPct. If a richer banner is ever wanted, the
 * backend's text changes, not this component.
 */
export function WarningBanner({ warning }) {
  if (!warning) return null;

  return (
    <div className="mb-4 flex items-start gap-2.5 rounded-DEFAULT border border-warn-border bg-warn-bg px-4 py-3.5">
      <TriangleAlert className="mt-0.5 h-[18px] w-[18px] flex-none text-warn" strokeWidth={1.6} />
      <div className="text-[13.5px] font-semibold text-warn">{warning.text}</div>
    </div>
  );
}
