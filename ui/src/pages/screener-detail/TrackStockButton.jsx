import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { addStock } from "../../api/stocks";

/**
 * @param {{ ticker: string, showToast: (message: string, tone?: "good"|"neutral") => void }} props
 * Promotes a screener ticker straight to the tracked watchlist -- the same
 * POST /api/stocks call and toast wording as the dashboard's AddStockModal
 * (Phase 11b), but skips the free-text ticker input: the ticker is already
 * known and already resolved (this page only renders once the live fetch
 * for it succeeded), so re-asking for it would be redundant friction.
 * There's no inline-422 path here (no field to correct) -- both the rare
 * 422 and the more likely 409 (already tracked) surface as a toast.
 */
export function TrackStockButton({ ticker, showToast }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => addStock(ticker),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      showToast(
        data.historyFetched
          ? `${data.ticker} added to your watchlist.`
          : `${data.ticker} added — price data will load on the next refresh.`,
        "good",
      );
    },
    onError: (err) => {
      showToast(err.message, "neutral");
    },
  });

  return (
    <button
      type="button"
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending || mutation.isSuccess}
      className="inline-flex items-center gap-1.5 rounded-lg border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white hover:bg-accent-ink disabled:opacity-50"
    >
      <Plus className="h-[15px] w-[15px]" strokeWidth={2} />
      {mutation.isPending ? "Adding…" : mutation.isSuccess ? "Added" : "Track this stock"}
    </button>
  );
}
