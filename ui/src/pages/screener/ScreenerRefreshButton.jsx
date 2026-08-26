import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postScreenerRefresh } from "../../api/screener";
import { fmtRefreshSummary } from "../../lib/format";

/**
 * Triggers POST /api/screener/refresh on demand -- runs the full screener
 * batch job and invalidates the cached results so the table and "Last
 * screened" timestamp reflect the new run. Same partial-failure notice
 * pattern as the dashboard's RefreshButton.
 *
 * @param {{ label?: string }} props - label defaults to "Refresh"; the
 *   never-run empty state passes "Run screener" instead.
 */
export function ScreenerRefreshButton({ label = "Refresh" }) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: postScreenerRefresh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["screener"] });
    },
  });

  const summary = mutation.data ? fmtRefreshSummary(mutation.data) : null;

  return (
    <div className="flex flex-col items-end gap-2">
      <button
        type="button"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending}
        className="rounded-lg border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white hover:bg-accent-ink disabled:opacity-50"
      >
        {mutation.isPending ? "Refreshing…" : label}
      </button>

      {(summary || mutation.isError) && (
        <div className="rounded-lg border border-warn-border bg-warn-bg px-3 py-2.5 text-[13px] text-warn">
          {mutation.isError ? mutation.error.message : summary}
        </div>
      )}
    </div>
  );
}
