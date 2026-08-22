import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "../../components/ui/dialog";
import { ActionBadge } from "../../components/badge/ActionBadge";
import { putTrade } from "../../api/trades";

const fieldClass =
  "rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

/**
 * @param {{
 *   trade: import('../../api/types').TradeHistoryEntry | null,
 *   onClose: () => void,
 * }} props
 * Edit-trade dialog, open whenever `trade` is non-null. Ticker and action
 * are read-only (contract: not editable via PUT) -- only shares/price/date
 * are editable fields, pre-filled from the row. Client-side validation is
 * required/positive-number only, same as TradeModal; the sequence-oversell
 * 422 (and any other) is rendered here verbatim. Can't be dismissed while
 * saving.
 */
export function EditTradeModal({ trade, onClose }) {
  const open = trade != null;
  const queryClient = useQueryClient();
  const [shares, setShares] = useState("");
  const [price, setPrice] = useState("");
  const [date, setDate] = useState("");

  const mutation = useMutation({
    mutationFn: (payload) => putTrade(trade.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trades"] });
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      onClose();
    },
  });

  useEffect(() => {
    if (!trade) return;
    setShares(String(trade.shares));
    setPrice(String(trade.pricePerShare));
    setDate(trade.date);
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trade]);

  function handleSubmit(e) {
    e.preventDefault();
    mutation.mutate({
      shares: Number(shares),
      pricePerShare: Number(price),
      date,
    });
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (mutation.isPending) return;
        if (!next) onClose();
      }}
    >
      <DialogContent className="w-full max-w-[440px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[440px]">
        <DialogTitle className="text-base font-bold">Edit trade</DialogTitle>

        {trade && (
          <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <span className="text-[12.5px] font-bold text-ink-muted">Stock</span>
              <div className={`${fieldClass} flex items-center justify-between bg-surface-sunken`}>
                <span>
                  {trade.ticker} · {trade.companyName}
                </span>
                <ActionBadge action={trade.action} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="edit-trade-shares" className="text-[12.5px] font-bold text-ink-muted">
                  Number of shares
                </label>
                <input
                  id="edit-trade-shares"
                  type="number"
                  className={`num ${fieldClass}`}
                  min="0.000001"
                  step="any"
                  required
                  value={shares}
                  onChange={(e) => setShares(e.target.value)}
                  disabled={mutation.isPending}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="edit-trade-price" className="text-[12.5px] font-bold text-ink-muted">
                  Price per share
                </label>
                <input
                  id="edit-trade-price"
                  type="number"
                  className={`num ${fieldClass}`}
                  min="0.01"
                  step="0.01"
                  required
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  disabled={mutation.isPending}
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="edit-trade-date" className="text-[12.5px] font-bold text-ink-muted">
                Date
              </label>
              <input
                id="edit-trade-date"
                type="date"
                className={fieldClass}
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
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
                {mutation.isPending ? "Saving…" : "Save changes"}
              </button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
