import { useEffect } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChartNoAxesCombined } from "lucide-react";
import { getStockDetail } from "../../api/stocks";
import { Panel } from "../../components/panel/Panel";
import { SuggestionChecklist } from "../../components/checklist/SuggestionChecklist";
import { PriceVolumeChart } from "../../components/charts/PriceVolumeChart";
import { DetailHeader } from "./DetailHeader";
import { WarningBanner } from "./WarningBanner";
import { InsufficientHistoryPanel } from "./InsufficientHistoryPanel";
import { IndicatorsPanel } from "./IndicatorsPanel";
import { PositionCard } from "./PositionCard";
import { AnalysisCard } from "./AnalysisCard";
import { NewsLinksPanel } from "./NewsLinksPanel";

function BackLink() {
  return (
    <Link
      to="/"
      className="mb-3.5 inline-flex items-center gap-1.5 text-[13px] font-semibold text-ink-muted no-underline hover:text-ink"
    >
      <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.8} />
      Back to dashboard
    </Link>
  );
}

/** The two-column head: id/price/badge/timestamp on the left, a
 * border-split "why" box (checklist or insufficient-history message) on
 * the right -- matches the reference's `.detail-head` / `.checklist-box`. */
function DetailHead({ children, ...headerProps }) {
  return (
    <div className="mb-4 grid grid-cols-1 gap-7 rounded-DEFAULT border border-border bg-surface p-6 shadow-card sm:grid-cols-[1.05fr_1.4fr]">
      <DetailHeader {...headerProps} />
      <div className="border-t border-border pt-4 sm:border-t-0 sm:border-l sm:pt-0 sm:pl-6.5">{children}</div>
    </div>
  );
}

export function StockDetailPage() {
  const { ticker } = useParams();
  const { setMeta } = useOutletContext();
  const { data, error, isPending } = useQuery({
    queryKey: ["stock", ticker],
    queryFn: () => getStockDetail(ticker),
  });

  useEffect(() => {
    setMeta(data?.meta);
  }, [data, setMeta]);

  if (isPending) {
    return (
      <div>
        <BackLink />
        <p className="py-20 text-center text-ink-muted">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <BackLink />
        <p className="py-20 text-center text-bad">{error.message}</p>
      </div>
    );
  }

  if (data.status === "insufficient_history") {
    return (
      <div>
        <BackLink />
        <DetailHead
          ticker={data.ticker}
          companyName={data.companyName}
          currentPrice={data.currentPrice}
          change1dPct={data.change1dPct}
          badgeLabel="INSUFFICIENT"
          meta={data.meta}
        >
          <InsufficientHistoryPanel
            daysOfHistoryAvailable={data.daysOfHistoryAvailable}
            daysOfHistoryRequired={data.daysOfHistoryRequired}
            tradingDaysUntilReady={data.tradingDaysUntilReady}
          />
        </DetailHead>
        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1.55fr_1fr]">
          <Panel title="30-day price & volume">
            <div className="flex h-[200px] flex-col items-center justify-center gap-1.5 text-center text-[13px] text-ink-faint">
              <ChartNoAxesCombined className="h-[26px] w-[26px]" strokeWidth={1.5} />
              <span>Not enough price history yet to draw a chart.</span>
            </div>
          </Panel>
          <div className="flex flex-col gap-4">
            <Panel title="My analysis">
              <AnalysisCard ticker={data.ticker} analysis={data.analysis} />
            </Panel>
            <Panel title="News & further reading">
              <NewsLinksPanel newsLinks={data.newsLinks} />
            </Panel>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <BackLink />
      <WarningBanner warning={data.warning} />
      <DetailHead
        ticker={data.ticker}
        companyName={data.companyName}
        currentPrice={data.currentPrice}
        change1dPct={data.change1dPct}
        badgeLabel={data.suggestion.label}
        meta={data.meta}
      >
        <SuggestionChecklist suggestion={data.suggestion} />
      </DetailHead>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[1.55fr_1fr]">
        <div className="flex flex-col gap-4">
          <Panel title="30-day price & volume" subtitle="Closing prices, delayed up to 15 minutes">
            <PriceVolumeChart chart={data.chart} change7dPct={data.indicators.change7dPct} />
          </Panel>
          <Panel title="Indicators">
            <IndicatorsPanel indicators={data.indicators} />
          </Panel>
        </div>
        <div className="flex flex-col gap-4">
          {data.position && (
            <Panel title="Your position">
              <PositionCard ticker={data.ticker} position={data.position} />
            </Panel>
          )}
          <Panel title="My analysis">
            <AnalysisCard ticker={data.ticker} analysis={data.analysis} />
          </Panel>
          <Panel title="News & further reading">
            <NewsLinksPanel newsLinks={data.newsLinks} />
          </Panel>
        </div>
      </div>
    </div>
  );
}
