import { useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getStocks } from "../../api/stocks";
import { SummaryStrip } from "../../components/summary/SummaryStrip";
import { StockTable } from "./StockTable";

export function DashboardPage() {
  const { setMeta } = useOutletContext();
  const { data, error, isPending } = useQuery({
    queryKey: ["stocks"],
    queryFn: getStocks,
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
        <h1 className="text-xl font-bold tracking-tight">Dashboard</h1>
        <div className="text-[13px] text-ink-muted">
          {data.stocks.length}-stock watchlist &middot; stocks needing attention are sorted to the top
        </div>
      </div>
      {data.summary && <SummaryStrip summary={data.summary} />}
      <StockTable stocks={data.stocks} />
    </div>
  );
}
