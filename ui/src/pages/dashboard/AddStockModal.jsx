import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "../../components/ui/dialog";
import { addStock } from "../../api/stocks";

const fieldClass =
  "rounded-sm border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

/**
 * @param {{
 *   open: boolean, onClose: () => void,
 *   showToast: (message: string, tone?: "good" | "neutral") => void,
 * }} props
 * Add-to-watchlist dialog. Client-side validation is non-empty only -- the
 * backend is the sole authority on whether a ticker actually resolves.
 * 422 (unknown ticker) renders inline and keeps the modal open so the user
 * can correct the symbol; 409 (already on the watchlist) and success both
 * close the modal and hand off to a toast instead, same
 * can't-dismiss-while-submitting pattern as TradeModal/CashModal.
 */
export function AddStockModal({ open, onClose, showToast }) {
  const queryClient = useQueryClient();
  const [ticker, setTicker] = useState("");

  const mutation = useMutation({
    mutationFn: (t) => addStock(t),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      onClose();
      showToast(
        data.historyFetched
          ? `${data.ticker} added to your watchlist.`
          : `${data.ticker} added — price data will load on the next refresh.`,
        "good"
      );
    },
    onError: (err) => {
      if (err.status === 409) {
        onClose();
        showToast(err.message, "neutral");
      }
      // 422: no-op here -- mutation.error renders inline below, modal stays open
    },
  });

  useEffect(() => {
    if (!open) return;
    setTicker("");
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function handleSubmit(e) {
    e.preventDefault();
    mutation.mutate(ticker);
  }

  const showInlineError = mutation.isError && mutation.error.status !== 409;

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (mutation.isPending) return;
        if (!next) onClose();
      }}
    >
      <DialogContent className="w-full max-w-[400px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[400px]">
        <DialogTitle className="text-base font-bold">Add to watchlist</DialogTitle>

        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="add-stock-ticker" className="text-[12.5px] font-bold text-ink-muted">
              Ticker symbol
            </label>
            <input
              id="add-stock-ticker"
              type="text"
              className={`num ${fieldClass}`}
              placeholder="e.g. PLTR"
              required
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              disabled={mutation.isPending}
              autoFocus
            />
          </div>

          {showInlineError && (
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
              disabled={mutation.isPending || !ticker.trim()}
              className="rounded-sm border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white transition-colors hover:bg-accent-ink active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
            >
              {mutation.isPending ? "Adding…" : "Add"}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
