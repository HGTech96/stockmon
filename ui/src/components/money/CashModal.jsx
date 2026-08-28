import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "../ui/dialog";
import { postCashEvent } from "../../api/cash";
import { fmtMoney } from "../../lib/format";

function todayIsoDate() {
  const d = new Date();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

const fieldClass =
  "rounded-sm border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

const TITLE = { deposit: "Deposit cash", withdraw: "Withdraw cash" };
const SUBMIT_LABEL = { deposit: "Save deposit", withdraw: "Save withdrawal" };

/**
 * @param {{
 *   type: "deposit" | "withdraw" | null,
 *   cashAvailable: number | undefined,
 *   onClose: () => void,
 * }} props
 * Deposit/withdraw dialog, open whenever `type` is non-null -- same
 * "open = value != null" convention as EditTradeModal's `trade` prop. The
 * withdraw form shows a display-only "Available: $X" caption from
 * `cashAvailable` (already fetched by the page, no extra request) so the
 * everyday case avoids the 422 rather than just explaining it after the
 * fact; the 422 itself ("Can't withdraw more than your available cash.")
 * remains the authoritative backstop and is rendered here verbatim, same
 * pattern as TradeModal. Can't be dismissed while submitting.
 */
export function CashModal({ type, cashAvailable, onClose }) {
  const open = type != null;
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(todayIsoDate());

  const mutation = useMutation({
    mutationFn: postCashEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["cash"] });
      onClose();
    },
  });

  useEffect(() => {
    if (!open) return;
    setAmount("");
    setDate(todayIsoDate());
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function handleSubmit(e) {
    e.preventDefault();
    mutation.mutate({
      type,
      amountUsd: Number(amount),
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
      <DialogContent className="w-full max-w-[400px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[400px]">
        <DialogTitle className="text-base font-bold">{type && TITLE[type]}</DialogTitle>

        {type && (
          <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="cash-amount" className="text-[12.5px] font-bold text-ink-muted">
                Amount
              </label>
              <input
                id="cash-amount"
                type="number"
                className={`num ${fieldClass}`}
                min="0.01"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={mutation.isPending}
              />
              {type === "withdraw" && cashAvailable != null && (
                <span className="text-[12.5px] text-ink-muted">Available: {fmtMoney(cashAvailable)}</span>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="cash-date" className="text-[12.5px] font-bold text-ink-muted">
                Date
              </label>
              <input
                id="cash-date"
                type="date"
                className={fieldClass}
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
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
                {mutation.isPending ? "Saving…" : SUBMIT_LABEL[type]}
              </button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
