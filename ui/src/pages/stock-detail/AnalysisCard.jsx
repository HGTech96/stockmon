import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { deleteAnalysis } from "../../api/stocks";
import { fmtDateLong, fmtMoney, fmtPrice, fmtToGo } from "../../lib/format";
import { AnalysisModal } from "./AnalysisModal";

/**
 * @param {{ ticker: string, analysis: import('../../api/types').Analysis | null }} props
 * Shows the stored analysis note (date + dollar value) or an empty state,
 * with Edit/Add and Clear actions. Independent of ownership -- rendered on
 * the detail page for owned and unowned stocks alike.
 */
export function AnalysisCard({ ticker, analysis }) {
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();

  const clearMutation = useMutation({
    mutationFn: () => deleteAnalysis(ticker),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["stock"] }),
  });

  return (
    <div>
      {analysis ? (
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-x-5 gap-y-3">
            <div>
              <div className="mb-1 text-[11px] font-semibold text-ink-muted">Date</div>
              <div className="text-[15px] font-semibold">{fmtDateLong(analysis.date)}</div>
            </div>
            <div>
              <div className="mb-1 text-[11px] font-semibold text-ink-muted">Value</div>
              <div className="num text-[15px] font-semibold">{fmtPrice(analysis.value)}</div>
            </div>
          </div>

          {analysis.progress && (
            <div className="border-t border-border pt-3.5">
              <div className="mb-1.5 flex items-center justify-between text-[12px]">
                <span className="text-ink-muted">Progress to analysis</span>
                <strong className="num text-[13px] font-semibold text-ink">
                  {fmtMoney(analysis.progress.progressPrice)} of {fmtMoney(analysis.progress.targetPrice)}
                </strong>
              </div>
              <div className="h-1.5 overflow-hidden rounded-pill bg-surface-sunken">
                <div
                  className="h-full rounded-pill bg-accent transition-[width] duration-500 ease-out"
                  style={{ width: `${(analysis.progress.progressPrice / analysis.progress.targetPrice) * 100}%` }}
                />
              </div>
              <div className="mt-1.5 text-[12px] text-ink-muted">
                {fmtToGo(analysis.progress.remainingPrice, analysis.progress.reached)}
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="text-[12px] font-semibold text-accent transition-colors hover:text-accent-ink hover:underline"
            >
              Edit
            </button>
            <button
              type="button"
              onClick={() => clearMutation.mutate()}
              disabled={clearMutation.isPending}
              className="text-[12px] font-semibold text-ink-muted transition-colors hover:text-ink hover:underline disabled:pointer-events-none disabled:opacity-50"
            >
              {clearMutation.isPending ? "Clearing…" : "Clear"}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-ink-faint">No analysis recorded</span>
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="text-[12px] font-semibold text-accent transition-colors hover:text-accent-ink hover:underline"
          >
            Add analysis
          </button>
        </div>
      )}

      <AnalysisModal
        ticker={editing ? ticker : null}
        currentDate={analysis?.date}
        currentValue={analysis?.value}
        onClose={() => setEditing(false)}
      />
    </div>
  );
}
