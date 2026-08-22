import { SummaryStrip } from "../../components/summary/SummaryStrip";
import { MoneyStrip } from "../../components/money/MoneyStrip";

/** @type {import('../../api/types').Summary} */
const mockSummary = {
  totalInvested: 1250.0,
  totalCurrentValue: 1421.0,
  totalProfitLoss: 171.0,
  totalProfitLossPct: 13.68,
};

/**
 * @type {import('../../api/types').Money}
 * Tells the recycling story: 100 deposited, 140 available -- the $40 gap
 * is realizedEarned recycled back into cash, per the phase 9b design doc.
 */
const mockMoney = {
  cashAvailable: 140.0,
  netDeposited: 100.0,
  realizedEarned: 40.0,
  realizedLost: 12.0,
  unrealizedGainOpen: 96.0,
  unrealizedLossOpen: 18.0,
};

/**
 * Phase 9b design-only preview: how the six-figure money block joins the
 * existing dashboard summary strip. Standalone route, deliberately NOT
 * wrapped by AppShell (AppShell mounts useDataRefresh, which fires a real
 * POST /api/refresh on an interval -- this page must never touch the
 * network). Hardcoded data only; remove this route in phase 9d once the
 * design is approved and wired to the real endpoints.
 */
export function CashPreviewPage() {
  return (
    <div className="min-h-screen bg-bg">
      <div className="border-b border-border-strong bg-accent-soft px-7 py-2.5 text-[13px] font-medium text-accent-ink">
        Phase 9b design preview — /preview/cash — hardcoded data, no API calls, temporary route
      </div>

      <main className="mx-auto max-w-[1360px] px-7 pt-7 pb-20">
        <h1 className="mb-5 text-xl font-bold tracking-tight">Dashboard</h1>

        <SummaryStrip summary={mockSummary} />
        <MoneyStrip money={mockMoney} />
      </main>
    </div>
  );
}
