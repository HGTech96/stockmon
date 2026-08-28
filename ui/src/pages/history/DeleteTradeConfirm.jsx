import { useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Dialog, DialogContent, DialogTitle } from "../../components/ui/dialog";
import { deleteTrade } from "../../api/trades";

/**
 * @param {{
 *   trade: import('../../api/types').TradeHistoryEntry | null,
 *   onClose: () => void,
 * }} props
 * First confirm-dialog pattern in the app (see phase-8 plan's tech-debt
 * note on the two divergent modal conventions) -- mirrors TradeModal's
 * hand-rolled style rather than the unused shadcn Button/DialogFooter
 * primitives, for consistency with EditTradeModal and TradeModal. States
 * the downstream effect up front; the backend's 422 (a later sell of this
 * ticker depends on the trade) is rendered inline, never re-derived
 * client-side. Can't be dismissed while deleting.
 */
export function DeleteTradeConfirm({ trade, onClose }) {
  const open = trade != null;
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => deleteTrade(trade.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trades"] });
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      onClose();
    },
  });

  useEffect(() => {
    if (!trade) return;
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trade]);

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (mutation.isPending) return;
        if (!next) onClose();
      }}
    >
      <DialogContent className="w-full max-w-[420px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[420px]">
        <DialogTitle className="text-base font-bold">Delete trade</DialogTitle>

        {trade && (
          <div className="mt-4 flex flex-col gap-4">
            <p className="text-[13.5px] leading-relaxed text-ink-muted">
              This changes your <span className="font-bold text-ink">{trade.ticker}</span> position and may affect
              later trades. This can&rsquo;t be undone.
            </p>

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
                type="button"
                onClick={() => mutation.mutate()}
                disabled={mutation.isPending}
                className="rounded-sm border border-bad bg-bad px-4 py-2.5 text-[13.5px] font-semibold text-white transition-colors hover:bg-bad/90 active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
              >
                {mutation.isPending ? "Deleting…" : "Delete trade"}
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
