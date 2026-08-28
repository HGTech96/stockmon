import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { getPortfolio } from "../../api/portfolio";
import { getStocks } from "../../api/stocks";
import { SummaryStrip } from "../../components/summary/SummaryStrip";
import { MoneyStrip } from "../../components/money/MoneyStrip";
import { EmptyMoneyStrip } from "../../components/money/EmptyMoneyStrip";
import { CashModal } from "../../components/money/CashModal";
import { PositionsTable } from "./PositionsTable";
import { EmptyState } from "./EmptyState";
import { TradeModal } from "./TradeModal";

export function PortfolioPage() {
  const { setMeta } = useOutletContext();
  const [modalOpen, setModalOpen] = useState(false);
  const [cashModalType, setCashModalType] = useState(null);

  const { data, error, isPending } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getPortfolio,
  });
  // Shared cache entry with Dashboard -- gives the trade modal price/company-name
  // lookups without a fetch of its own; see docs/planning/phase-5c-portfolio.md.
  const { data: stocksData } = useQuery({
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

  const stocksByTicker = new Map(
    (stocksData?.stocks ?? []).map((s) => [s.ticker, { companyName: s.companyName, currentPrice: s.currentPrice }]),
  );
  const ownedTickers = new Set(data.positions.map((p) => p.ticker));

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-4">
        <h1 className="text-xl font-bold tracking-tight">Portfolio</h1>
        <div className="text-[13px] text-ink-muted">
          {data.hasTrades ? `${data.positions.length} position${data.positions.length === 1 ? "" : "s"}` : "Your recorded positions"}
        </div>
      </div>

      {data.summary && <SummaryStrip summary={data.summary} />}
      {data.money ? (
        <MoneyStrip money={data.money} onDeposit={() => setCashModalType("deposit")} onWithdraw={() => setCashModalType("withdraw")} />
      ) : (
        <EmptyMoneyStrip onDeposit={() => setCashModalType("deposit")} />
      )}

      {data.hasTrades ? (
        <>
          <div className="mb-3.5 flex justify-end">
            <button
              type="button"
              onClick={() => setModalOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-sm border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white transition-colors hover:bg-accent-ink active:translate-y-px"
            >
              <Plus className="h-[15px] w-[15px]" strokeWidth={2} />
              Add trade
            </button>
          </div>
          <PositionsTable positions={data.positions} />
        </>
      ) : (
        <EmptyState onAddTrade={() => setModalOpen(true)} />
      )}

      <TradeModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        watchlist={data.watchlist}
        stocksByTicker={stocksByTicker}
        ownedTickers={ownedTickers}
      />

      <CashModal type={cashModalType} cashAvailable={data.money?.cashAvailable} onClose={() => setCashModalType(null)} />
    </div>
  );
}
