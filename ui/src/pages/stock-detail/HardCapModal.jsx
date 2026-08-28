import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "../../components/ui/dialog";
import { putPositionTarget } from "../../api/settings";

const fieldClass =
  "rounded-sm border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

/**
 * @param {{
 *   ticker: string | null,
 *   currentTargetDollars: number | undefined,
 *   onClose: () => void,
 * }} props
 * Sets this stock's hard-cap override -- open whenever `ticker` is
 * non-null, same "open = value != null" convention as CashModal/
 * EditTradeModal. Resetting an override back to the default happens on
 * the Settings page, not here, to keep this form single-purpose.
 */
export function HardCapModal({ ticker, currentTargetDollars, onClose }) {
  const open = ticker != null;
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState("");

  const mutation = useMutation({
    mutationFn: () => putPositionTarget(ticker, { targetDollars: Number(amount) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stock"] });
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      onClose();
    },
  });

  useEffect(() => {
    if (!open) return;
    setAmount(String(currentTargetDollars ?? ""));
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, currentTargetDollars]);

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (mutation.isPending) return;
        if (!next) onClose();
      }}
    >
      <DialogContent className="w-full max-w-[400px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[400px]">
        <DialogTitle className="text-base font-bold">Set hard cap{ticker ? ` — ${ticker}` : ""}</DialogTitle>

        {ticker && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
            className="mt-4 flex flex-col gap-4"
          >
            <div className="flex flex-col gap-1.5">
              <label htmlFor="hard-cap-amount" className="text-[12.5px] font-bold text-ink-muted">
                Amount
              </label>
              <input
                id="hard-cap-amount"
                type="number"
                className={`num ${fieldClass}`}
                min="0.01"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={mutation.isPending}
              />
            </div>

            {mutation.isError && (
              <div className="rounded-sm border border-warn-border bg-warn-bg px-3 py-2.5 text-[13px] text-warn">{mutation.error.message}</div>
            )}

            <div className="mt-1 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={onClose}
                disabled={mutation.isPending}
                className="rounded-sm border border-border-strong bg-surface px-4 py-2.5 text-[13.5px] font-semibold transition-colors hover:bg-surface-sunken active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={mutation.isPending}
                className="rounded-sm border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white transition-colors hover:bg-accent-ink active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
              >
                {mutation.isPending ? "Saving…" : "Save hard cap"}
              </button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
