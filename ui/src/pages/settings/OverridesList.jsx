import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { deletePositionTarget } from "../../api/settings";
import { fmtMoney } from "../../lib/format";

/**
 * @param {{ perPositionTargets: Object<string, number>, onReset: () => void }} props
 */
export function OverridesList({ perPositionTargets, onReset }) {
  const mutation = useMutation({
    mutationFn: (ticker) => deletePositionTarget(ticker),
    onSuccess: onReset,
  });
  const overrides = Object.entries(perPositionTargets);

  return (
    <div className="max-w-[420px]">
      <h2 className="mb-1 text-[14px] font-bold tracking-tight">Per-stock hard caps</h2>
      <p className="mb-4 text-[12.5px] text-ink-muted">
        Set from a stock's detail page. Reset here to fall back to the default above.
      </p>

      {overrides.length === 0 ? (
        <p className="text-[13px] text-ink-muted">No per-stock hard caps set.</p>
      ) : (
        <div className="divide-y divide-border overflow-hidden rounded-DEFAULT border border-border bg-surface shadow-card">
          {overrides.map(([ticker, dollars]) => (
            <div key={ticker} className="flex items-center justify-between px-4 py-3">
              <Link to={`/stocks/${ticker}`} className="text-[13.5px] font-semibold text-accent transition-colors hover:text-accent-ink hover:underline">
                {ticker}
              </Link>
              <div className="flex items-center gap-3">
                <span className="num text-[13.5px]">{fmtMoney(dollars)}</span>
                <button
                  type="button"
                  onClick={() => mutation.mutate(ticker)}
                  disabled={mutation.isPending}
                  className="rounded-sm border border-border-strong bg-surface px-3 py-1.5 text-[12.5px] font-semibold transition-colors hover:bg-surface-hover active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
                >
                  Reset to default
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      {mutation.isError && (
        <div className="mt-3 rounded-sm border border-warn-border bg-warn-bg px-3 py-2.5 text-[13px] text-warn">
          {mutation.error.message}
        </div>
      )}
    </div>
  );
}
