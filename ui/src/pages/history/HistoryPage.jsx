import { useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getTrades } from "../../api/trades";
import { TradeHistoryTable } from "./TradeHistoryTable";
import { EmptyState } from "./EmptyState";

export function HistoryPage() {
  const { setMeta } = useOutletContext();

  const { data, error, isPending } = useQuery({
    queryKey: ["trades"],
    queryFn: getTrades,
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
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-4">
        <h1 className="text-xl font-bold tracking-tight">History</h1>
        <div className="text-[13px] text-ink-muted">
          {data.trades.length} trade{data.trades.length === 1 ? "" : "s"}
        </div>
      </div>

      {data.trades.length > 0 ? <TradeHistoryTable trades={data.trades} /> : <EmptyState />}
    </div>
  );
}
