import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Info } from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "../../components/ui/dialog";
import { postTrade } from "../../api/trades";

function todayIsoDate() {
  const d = new Date();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${month}-${day}`;
}

const fieldClass =
  "rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

/**
 * @param {{
 *   open: boolean, onClose: () => void,
 *   watchlist: string[],
 *   stocksByTicker: Map<string, {companyName: string, currentPrice: number}>,
 *   ownedTickers: Set<string>,
 * }} props
 * Add-trade dialog. Client-side validation is required/positive-number
 * only (native `required`/`min` attributes) -- every other rule (sell
 * exceeds held shares, sell of no position, future date, ticker not on
 * watchlist) is the backend's 422, rendered here verbatim, never
 * duplicated. The dialog can't be dismissed (Escape, backdrop, close-X,
 * Cancel) while the trade is submitting, so a slow request never reads as
 * a silent failure.
 */
export function TradeModal({ open, onClose, watchlist, stocksByTicker, ownedTickers }) {
  const queryClient = useQueryClient();
  const [ticker, setTicker] = useState("");
  const [side, setSide] = useState("buy");
  const [shares, setShares] = useState("");
  const [price, setPrice] = useState("");
  const [date, setDate] = useState(todayIsoDate());

  const mutation = useMutation({
    mutationFn: postTrade,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
      onClose();
    },
  });

  useEffect(() => {
    if (!open) return;
    setTicker("");
    setSide("buy");
    setShares("");
    setPrice("");
    setDate(todayIsoDate());
    mutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function handleTickerChange(e) {
    const next = e.target.value;
    setTicker(next);
    const info = stocksByTicker.get(next);
    if (info) setPrice(info.currentPrice.toFixed(2));
    mutation.reset();
  }

  function handleSideChange(next) {
    setSide(next);
    mutation.reset();
  }

  function handleSubmit(e) {
    e.preventDefault();
    mutation.mutate({
      ticker,
      action: side,
      shares: Number(shares),
      pricePerShare: Number(price),
      date,
    });
  }

  const showHint = side === "buy" && ownedTickers.has(ticker);

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (mutation.isPending) return;
        if (!next) onClose();
      }}
    >
      <DialogContent className="w-full max-w-[440px] rounded-DEFAULT p-6 shadow-pop sm:max-w-[440px]">
        <DialogTitle className="text-base font-bold">Add trade</DialogTitle>

        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="trade-stock" className="text-[12.5px] font-bold text-ink-muted">
              Stock
            </label>
            <select id="trade-stock" className={fieldClass} value={ticker} onChange={handleTickerChange} required disabled={mutation.isPending}>
              <option value="" disabled>
                Choose a stock
              </option>
              {watchlist.map((t) => {
                const info = stocksByTicker.get(t);
                return (
                  <option key={t} value={t}>
                    {info ? `${t} · ${info.companyName}` : t}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-[12.5px] font-bold text-ink-muted">Trade type</span>
            <div className="flex overflow-hidden rounded-lg border border-border-strong">
              <button
                type="button"
                onClick={() => handleSideChange("buy")}
                disabled={mutation.isPending}
                className={`flex-1 py-2.5 text-[13px] font-semibold ${side === "buy" ? "bg-good-bg text-good" : "bg-surface text-ink-muted"}`}
              >
                Buy
              </button>
              <button
                type="button"
                onClick={() => handleSideChange("sell")}
                disabled={mutation.isPending}
                className={`flex-1 border-l border-border-strong py-2.5 text-[13px] font-semibold ${
                  side === "sell" ? "bg-warn-bg text-warn" : "bg-surface text-ink-muted"
                }`}
              >
                Sell
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3.5">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="trade-shares" className="text-[12.5px] font-bold text-ink-muted">
                Number of shares
              </label>
              <input
                id="trade-shares"
                type="number"
                className={`num ${fieldClass}`}
                min="1"
                step="1"
                required
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                disabled={mutation.isPending}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="trade-price" className="text-[12.5px] font-bold text-ink-muted">
                Price per share
              </label>
              <input
                id="trade-price"
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
            <label htmlFor="trade-date" className="text-[12.5px] font-bold text-ink-muted">
              Date
            </label>
            <input
              id="trade-date"
              type="date"
              className={fieldClass}
              required
              value={date}
              onChange={(e) => setDate(e.target.value)}
              disabled={mutation.isPending}
            />
          </div>

          {showHint && (
            <div className="flex items-start gap-1.5 rounded-lg bg-accent-soft px-2.5 py-2 text-xs text-accent-ink">
              <Info className="mt-0.5 h-3.5 w-3.5 flex-none" strokeWidth={1.6} />
              <span>This will update your average purchase price for this stock.</span>
            </div>
          )}

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
              {mutation.isPending ? "Saving…" : "Save trade"}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
