import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./pages/dashboard/DashboardPage";
import { StockDetailPage } from "./pages/stock-detail/StockDetailPage";
import { PortfolioPage } from "./pages/portfolio/PortfolioPage";
import { HistoryPage } from "./pages/history/HistoryPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="stocks/:ticker" element={<StockDetailPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="history" element={<HistoryPage />} />
      </Route>
    </Routes>
  );
}
