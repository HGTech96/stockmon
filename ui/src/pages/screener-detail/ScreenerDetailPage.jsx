import { useEffect } from "react";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ChartNoAxesCombined } from "lucide-react";
import { getScreenerDetail } from "../../api/screener";
import { Panel } from "../../components/panel/Panel";
import { SuggestionChecklist } from "../../components/checklist/SuggestionChecklist";
import { PriceVolumeChart } from "../../components/charts/PriceVolumeChart";
import { Toast } from "../../components/toast/Toast";
import { useToast } from "../../components/toast/useToast";
import { DetailHeader } from "../stock-detail/DetailHeader";
import { WarningBanner } from "../stock-detail/WarningBanner";
import { InsufficientHistoryPanel } from "../stock-detail/InsufficientHistoryPanel";
import { IndicatorsPanel } from "../stock-detail/IndicatorsPanel";
import { NewsLinksPanel } from "../stock-detail/NewsLinksPanel";
import { TrackStockButton } from "./TrackStockButton";

function BackLink() {
  return (
    <Link
      to="/screener"
      className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-ink-muted no-underline transition-colors hover:text-ink"
    >
      <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.8} />
      Back to screener
    </Link>
  );
}

/** Same two-column head as the tracked stock detail page (Phase 5) --
 * id/price/badge/timestamp on the left, checklist or insufficient-history
 * message on the right. */
function DetailHead({ children, ...headerProps }) {
  return (
    <div className="mb-4 grid grid-cols-1 gap-7 rounded-DEFAULT border border-border bg-surface p-6 shadow-card sm:grid-cols-[1.05fr_1.4fr]">
      <DetailHeader {...headerProps} />
      <div className="border-t border-border pt-4 sm:border-t-0 sm:border-l sm:pt-0 sm:pl-6.5">{children}</div>
    </div>
  );
}

/**
 * Screener's live-fetch detail view -- same shape and same shell components
 * as the tracked stock detail page, fed by GET /api/screener/{ticker}/detail
 * instead. `position` is always null on this endpoint (screener stocks are
 * never owned), so there's no position card; "Track this stock" takes its
 * place as the page's primary action.
 */
export function ScreenerDetailPage() {
  const { ticker } = useParams();
  const { setMeta } = useOutletContext();
  const toast = useToast();
  const { data, error, isPending } = useQuery({
    queryKey: ["screenerDetail", ticker],
    queryFn: () => getScreenerDetail(ticker),
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

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <BackLink />
        <TrackStockButton ticker={data.ticker} showToast={toast.show} />
      </div>

      {data.status === "insufficient_history" ? (
        <>
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
            <Panel title="News & further reading">
              <NewsLinksPanel newsLinks={data.newsLinks} />
            </Panel>
          </div>
        </>
      ) : (
        <>
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
              <Panel title="News & further reading">
                <NewsLinksPanel newsLinks={data.newsLinks} />
              </Panel>
            </div>
          </div>
        </>
      )}

      <Toast message={toast.message} tone={toast.tone} />
    </div>
  );
}
