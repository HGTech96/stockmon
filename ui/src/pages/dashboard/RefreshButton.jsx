import { useMutation, useQueryClient } from "@tanstack/react-query";
import { postRefresh } from "../../api/refresh";
import { fmtRefreshSummary } from "../../lib/format";

/**
 * Triggers POST /api/refresh on demand and invalidates the dashboard's data
 * so the table, money strip, and freshness timestamp reflect the result.
 * Partial failures are named inline rather than silently dropped, per the
 * app's honesty principle -- a stale price should be visible, not hidden.
 */
export function RefreshButton() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: postRefresh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["cash"] });
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
        {mutation.isPending ? "Refreshing…" : "Refresh now"}
      </button>

      {(summary || mutation.isError) && (
        <div className="rounded-lg border border-warn-border bg-warn-bg px-3 py-2.5 text-[13px] text-warn">
          {mutation.isError ? mutation.error.message : summary}
        </div>
      )}
    </div>
  );
}
