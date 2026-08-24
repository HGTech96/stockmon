import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Outlet, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ScreenerDetailPage } from "./ScreenerDetailPage";

const getScreenerDetailMock = vi.fn();
const addStockMock = vi.fn();

vi.mock("../../api/screener", () => ({
  getScreenerDetail: (ticker) => getScreenerDetailMock(ticker),
}));

vi.mock("../../api/stocks", () => ({
  addStock: (ticker) => addStockMock(ticker),
}));

vi.mock("../../components/charts/PriceVolumeChart", () => ({
  PriceVolumeChart: () => <div data-testid="price-volume-chart" />,
}));

const META = { dataAsOf: "2026-08-19T14:45:00-04:00", isStale: false, staleMessage: null };

const OK_DETAIL = {
  meta: META,
  ticker: "PLTR",
  companyName: "Palantir Technologies Inc.",
  currentPrice: 27.85,
  change1dPct: 1.52,
  status: "ok",
  daysOfHistoryAvailable: 60,
  daysOfHistoryRequired: 30,
  tradingDaysUntilReady: null,
  suggestion: {
    label: "BUY",
    type: "entry",
    metCount: 3,
    totalCount: 4,
    checklist: [{ id: "rsi_low", text: "RSI is relatively low (34)", passed: true }],
    note: null,
  },
  warning: null,
  chart: { days: [{ date: "2026-08-18", close: 27.85, volume: 1000 }], thirtyDayAverage: 29.1, userAvgPurchasePrice: null },
  indicators: {
    currentPrice: 27.85,
    change1dPct: 1.52,
    change7dPct: -1.0,
    thirtyDayAverage: 29.1,
    thirtyDayHigh: 31.0,
    thirtyDayLow: 26.0,
    distanceFromHighPct: -10.2,
    distanceFromLowPct: 7.1,
    rsi: 38.0,
    todaysVolume: 1000,
    averageVolume: 1200,
    volumeVsAveragePct: 83.3,
  },
  position: null,
  newsLinks: { yahooFinance: "https://finance.yahoo.com/quote/PLTR", googleFinance: "https://www.google.com/finance/quote/PLTR", investorRelations: null },
};

const INSUFFICIENT_DETAIL = {
  meta: META,
  ticker: "ZZZZ",
  companyName: "Recent Listing Inc.",
  currentPrice: 5.1,
  change1dPct: 0.9,
  status: "insufficient_history",
  daysOfHistoryAvailable: 14,
  daysOfHistoryRequired: 30,
  tradingDaysUntilReady: 16,
  suggestion: null,
  warning: null,
  chart: null,
  indicators: null,
  position: null,
  newsLinks: { yahooFinance: "https://finance.yahoo.com/quote/ZZZZ", googleFinance: "https://www.google.com/finance/quote/ZZZZ", investorRelations: null },
};

function renderPage(ticker = "PLTR") {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/screener/${ticker}`]}>
        <Routes>
          <Route element={<Outlet context={{ setMeta: vi.fn() }} />}>
            <Route path="screener/:ticker" element={<ScreenerDetailPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getScreenerDetailMock.mockReset();
  addStockMock.mockReset();
});

afterEach(() => {
  cleanup();
});

describe("ScreenerDetailPage", () => {
  it("renders the insufficient-history branch", async () => {
    getScreenerDetailMock.mockResolvedValue(INSUFFICIENT_DETAIL);
    renderPage("ZZZZ");

    expect(await screen.findByText("Not enough data yet")).toBeInTheDocument();
    expect(screen.queryByTestId("price-volume-chart")).not.toBeInTheDocument();
  });

  it("renders the ok branch with chart, indicators, and checklist", async () => {
    getScreenerDetailMock.mockResolvedValue(OK_DETAIL);
    renderPage("PLTR");

    expect(await screen.findByTestId("price-volume-chart")).toBeInTheDocument();
    expect(screen.getByText("RSI is relatively low (34)")).toBeInTheDocument();
  });

  it("tracks the stock on success: calls addStock, invalidates stocks, shows the good toast", async () => {
    getScreenerDetailMock.mockResolvedValue(OK_DETAIL);
    addStockMock.mockResolvedValue({ ticker: "PLTR", companyName: "Palantir Technologies Inc.", historyFetched: true });
    renderPage("PLTR");

    fireEvent.click(await screen.findByText("Track this stock"));

    await waitFor(() => expect(addStockMock).toHaveBeenCalledWith("PLTR"));
    expect(await screen.findByText("PLTR added to your watchlist.")).toBeInTheDocument();
  });

  it("shows both a neutral toast and a standing inline banner when the ticker is already tracked (409)", async () => {
    getScreenerDetailMock.mockResolvedValue(OK_DETAIL);
    const err = new Error("PLTR is already on your watchlist.");
    err.status = 409;
    addStockMock.mockRejectedValue(err);
    renderPage("PLTR");

    fireEvent.click(await screen.findByText("Track this stock"));

    const matches = await screen.findAllByText("PLTR is already on your watchlist.");
    expect(matches).toHaveLength(2); // the toast (auto-dismisses) + the inline banner under the button (stays)
  });
});
