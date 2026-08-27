import { useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getScreener } from "../../api/screener";
import { fmtRelativeTime } from "../../lib/format";
import { ScreenerEmptyState } from "./ScreenerEmptyState";
import { ScreenerRefreshButton } from "./ScreenerRefreshButton";
import { ScreenerTable } from "./ScreenerTable";

export function ScreenerPage() {
  const { setMeta, screenerViewState } = useOutletContext();
  const { data, error, isPending } = useQuery({
    queryKey: ["screener"],
    queryFn: getScreener,
  });

  useEffect(() => {
    setMeta(data?.meta);
  }, [data, setMeta]);

  if (isPending) {
    return <p className="py-20 text-center text-ink-muted">Loading…</p>;
  }

  if (error) {
    return <p className="py-20 text-center text-bad">{error.message}</p>;
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Screener</h1>
          {data.runAt && (
            <div className="text-[13px] text-ink-muted">
              {data.results.length} stocks screened &middot; Last screened {fmtRelativeTime(data.runAt)}
            </div>
          )}
        </div>
        {data.runAt !== null && <ScreenerRefreshButton />}
      </div>

      {data.runAt === null ? <ScreenerEmptyState /> : <ScreenerTable results={data.results} viewState={screenerViewState} />}
    </div>
  );
}
