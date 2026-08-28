import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { ScreenerSection } from "./components/layout/ScreenerSection";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { StockDetailPage } from "./pages/stock-detail/StockDetailPage";
import { PortfolioPage } from "./pages/portfolio/PortfolioPage";
import { HistoryPage } from "./pages/history/HistoryPage";
import { ScreenerPage } from "./pages/screener/ScreenerPage";
import { ScreenerDetailPage } from "./pages/screener-detail/ScreenerDetailPage";
import { SettingsPage } from "./pages/settings/SettingsPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="stocks/:ticker" element={<StockDetailPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route element={<ScreenerSection />}>
          <Route path="screener" element={<ScreenerPage />} />
          <Route path="screener/:ticker" element={<ScreenerDetailPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
