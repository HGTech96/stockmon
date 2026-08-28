from datetime import date, timedelta
from decimal import Decimal

from stockmon.api.dependencies import get_market_data_provider
from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.main import app

DETAIL_TOP_KEYS = {
    "meta", "ticker", "companyName", "currentPrice", "change1dPct", "status",
    "daysOfHistoryAvailable", "daysOfHistoryRequired", "tradingDaysUntilReady",
    "suggestion", "warning", "chart", "indicators", "position", "analysis", "newsLinks",
}


class FakeProvider(MarketDataProvider):
    def __init__(
        self,
        history_by_ticker: dict[str, list[DailyBar]],
        failing_history_tickers: set[str] | None = None,
        failing_name_tickers: set[str] | None = None,
    ):
        self._history_by_ticker = history_by_ticker
        self._failing_history_tickers = failing_history_tickers or set()
        self._failing_name_tickers = failing_name_tickers or set()

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if ticker in self._failing_history_tickers:
            raise MarketDataError(f"download timeout for {ticker}")
        return self._history_by_ticker[ticker]

    def fetch_current_quote(self, ticker: str) -> Quote:
        raise NotImplementedError

    def fetch_company_name(self, ticker: str) -> str:
        if ticker in self._failing_name_tickers:
            raise MarketDataError(f"no name for {ticker}")
        return f"{ticker} Inc."

    def fetch_exchange(self, ticker: str) -> str | None:
        return None


def _bars(n: int, *, start: date = date(2026, 1, 1)) -> list[DailyBar]:
    return [
        DailyBar(
            date=start + timedelta(days=i),
            open=Decimal(100),
            high=Decimal(100),
            low=Decimal(100),
            close=Decimal(100),
            volume=1_000_000,
        )
        for i in range(n)
    ]


def _override_provider(provider: MarketDataProvider) -> None:
    app.dependency_overrides[get_market_data_provider] = lambda: provider


def test_valid_unowned_ticker_returns_full_shape(client) -> None:
    _override_provider(FakeProvider(history_by_ticker={"PLTR": _bars(30)}))
    try:
        r = client.get("/api/screener/PLTR/detail")
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == DETAIL_TOP_KEYS
    assert body["ticker"] == "PLTR"
    assert body["companyName"] == "PLTR Inc."
    assert body["status"] == "ok"
    assert body["suggestion"]["type"] == "entry"
    assert body["position"] is None
    assert body["analysis"] is None
    assert body["chart"]["userAvgPurchasePrice"] is None
    assert body["newsLinks"]["investorRelations"] is None


def test_unknown_ticker_is_422(client) -> None:
    _override_provider(FakeProvider(history_by_ticker={}, failing_name_tickers={"ZZZZ"}))
    try:
        r = client.get("/api/screener/ZZZZ/detail")
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 422
    assert r.json() == {"error": "Unknown ticker — check the symbol."}


def test_insufficient_history_ticker_returns_insufficient_state(client) -> None:
    _override_provider(FakeProvider(history_by_ticker={"NEWCO": _bars(14)}))
    try:
        r = client.get("/api/screener/NEWCO/detail")
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "insufficient_history"
    assert body["suggestion"] is None
    assert body["indicators"] is None
    assert body["chart"] is None
    assert body["daysOfHistoryAvailable"] == 14
    assert body["tradingDaysUntilReady"] == 16
