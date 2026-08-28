import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "../../components/ui/dialog";
import { putAnalysis } from "../../api/stocks";

const fieldClass =
  "rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

/**
 * @param {{
 *   ticker: string | null,
 *   currentDate: string | null | undefined,
 *   currentValue: number | null | undefined,
 *   onClose: () => void,
 * }} props
 * Sets this stock's analysis note (date + dollar value) -- open whenever
 * `ticker` is non-null, same "open = value != null" convention as
 * HardCapModal/CashModal. Applies to any watchlist stock, owned or not.
 */
export function AnalysisModal({ ticker, currentDate, currentValue, onClose }) {
  const open = ticker != null;
  const queryClient = useQueryClient();
  const [analysisDate, setAnalysisDate] = useState("");
  const [value, setValue] = useState("");

  const mutation = useMutation({
    mutationFn: () => putAnalysis(ticker, { date: analysisDate, value: Number(value) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stock"] });
      onClose();
    },
  });

  useEffect(() => {
    if (!open) return;
    setAnalysisDate(currentDate ?? "");
    setValue(String(currentValue ?? ""));
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, currentDate, currentValue]);

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (mutation.isPending) return;
        if (!next) onClose();
      }}
    >
      <DialogContent className="w-full max-w-[400px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[400px]">
        <DialogTitle className="text-base font-bold">Set analysis{ticker ? ` — ${ticker}` : ""}</DialogTitle>

        {ticker && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
            className="mt-4 flex flex-col gap-4"
          >
            <div className="flex flex-col gap-1.5">
              <label htmlFor="analysis-date" className="text-[12.5px] font-bold text-ink-muted">
                Date
              </label>
              <input
                id="analysis-date"
                type="date"
                className={fieldClass}
                required
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value)}
                disabled={mutation.isPending}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="analysis-value" className="text-[12.5px] font-bold text-ink-muted">
                Value
              </label>
              <input
                id="analysis-value"
                type="number"
                className={`num ${fieldClass}`}
                min="0.01"
                step="0.01"
                required
                value={value}
                onChange={(e) => setValue(e.target.value)}
                disabled={mutation.isPending}
              />
            </div>

            {mutation.isError && (
              <div className="rounded-lg border border-warn-border bg-warn-bg px-3 py-2.5 text-[13px] text-warn">{mutation.error.message}</div>
            )}

            <div className="mt-1 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={onClose}
                disabled={mutation.isPending}
                className="rounded-lg border border-border-strong bg-surface px-4 py-2.5 text-[13.5px] font-semibold hover:bg-surface-sunken disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={mutation.isPending}
                className="rounded-lg border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white hover:bg-accent-ink disabled:opacity-50"
              >
                {mutation.isPending ? "Saving…" : "Save analysis"}
              </button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
