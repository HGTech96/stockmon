import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getStocks } from "../../api/stocks";
import { SummaryStrip } from "../../components/summary/SummaryStrip";
import { Toast } from "../../components/toast/Toast";
import { useToast } from "../../components/toast/useToast";
import { AddStockButton } from "./AddStockButton";
import { AddStockModal } from "./AddStockModal";
import { RefreshButton } from "./RefreshButton";
import { StockTable } from "./StockTable";

export function DashboardPage() {
  const { setMeta } = useOutletContext();
  const [addStockOpen, setAddStockOpen] = useState(false);
  const toast = useToast();
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
      <div className="mb-3 flex items-start justify-end gap-2.5">
        <AddStockButton onClick={() => setAddStockOpen(true)} />
        <RefreshButton />
      </div>
      <StockTable stocks={data.stocks} />

      <AddStockModal open={addStockOpen} onClose={() => setAddStockOpen(false)} showToast={toast.show} />
      <Toast message={toast.message} tone={toast.tone} />
    </div>
  );
}
