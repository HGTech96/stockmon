from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.db.models import Stock
from stockmon.services.refresh_service import refresh_all_stocks


class FakeProvider(MarketDataProvider):
    def __init__(self, history_by_ticker: dict[str, list[DailyBar]], failing_tickers: set[str]):
        self._history_by_ticker = history_by_ticker
        self._failing_tickers = failing_tickers

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if ticker in self._failing_tickers:
            raise MarketDataError(f"download timeout for {ticker}")
        return self._history_by_ticker[ticker]

    def fetch_current_quote(self, ticker: str) -> Quote:
        raise NotImplementedError


def _make_bar(day: date) -> DailyBar:
    return DailyBar(
        date=day,
        open=Decimal("10.00"),
        high=Decimal("11.00"),
        low=Decimal("9.00"),
        close=Decimal("10.50"),
        volume=1000,
    )


def test_refresh_all_stocks_partial_failure() -> None:
    ok_stock = Stock(id=1, ticker="AAPL", company_name="Apple Inc.")
    failing_stock = Stock(id=2, ticker="KO", company_name="Coca-Cola Co.")

    db = MagicMock()
    db.query.return_value.all.return_value = [ok_stock, failing_stock]

    provider = FakeProvider(
        history_by_ticker={"AAPL": [_make_bar(date(2026, 8, 18))]},
        failing_tickers={"KO"},
    )

    with patch("stockmon.services.refresh_service.upsert_daily_prices") as mock_upsert:
        result = refresh_all_stocks(db, provider, days=60)

    assert result.refreshed == ["AAPL"]
    assert len(result.failed) == 1
    assert result.failed[0].ticker == "KO"
    assert result.failed[0].error == "download timeout for KO"

    mock_upsert.assert_called_once_with(db, ok_stock.id, provider.fetch_daily_history("AAPL", 60))
    db.commit.assert_called_once()
    db.rollback.assert_called_once()
