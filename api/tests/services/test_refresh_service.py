from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.db.models import Ticker
from stockmon.services.refresh_service import refresh_all_stocks, refresh_stock

USER_ID = 1


class FakeProvider(MarketDataProvider):
    def __init__(
        self,
        history_by_ticker: dict[str, list[DailyBar]],
        failing_tickers: set[str],
        quote_by_ticker: dict[str, Quote] | None = None,
        failing_quote_tickers: set[str] | None = None,
    ):
        self._history_by_ticker = history_by_ticker
        self._failing_tickers = failing_tickers
        self._quote_by_ticker = quote_by_ticker or {}
        self._failing_quote_tickers = failing_quote_tickers or set()
        self.quote_calls: list[str] = []

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if ticker in self._failing_tickers:
            raise MarketDataError(f"download timeout for {ticker}")
        return self._history_by_ticker[ticker]

    def fetch_current_quote(self, ticker: str) -> Quote:
        self.quote_calls.append(ticker)
        if ticker in self._failing_quote_tickers:
            raise MarketDataError(f"no quote for {ticker}")
        if ticker not in self._quote_by_ticker:
            raise MarketDataError(f"no quote configured for {ticker}")
        return self._quote_by_ticker[ticker]

    def fetch_company_name(self, ticker: str) -> str:
        raise NotImplementedError

    def fetch_exchange(self, ticker: str) -> str | None:
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
    ok_ticker = Ticker(id=1, ticker="AAPL", company_name="Apple Inc.")
    failing_ticker = Ticker(id=2, ticker="KO", company_name="Coca-Cola Co.")

    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [ok_ticker, failing_ticker]

    provider = FakeProvider(
        history_by_ticker={"AAPL": [_make_bar(date(2026, 8, 18))]},
        failing_tickers={"KO"},
    )

    with patch("stockmon.services.refresh_service.upsert_daily_prices") as mock_upsert:
        result = refresh_all_stocks(db, provider, USER_ID, days=60)

    assert result.refreshed == ["AAPL"]
    assert len(result.failed) == 1
    assert result.failed[0].ticker == "KO"
    assert result.failed[0].error == "download timeout for KO"

    mock_upsert.assert_called_once_with(db, ok_ticker.id, provider.fetch_daily_history("AAPL", 60))
    db.commit.assert_called_once()
    db.rollback.assert_called_once()


def test_refresh_stock_success_returns_none_and_commits() -> None:
    ticker = Ticker(id=1, ticker="AAPL", company_name="Apple Inc.")
    db = MagicMock()
    provider = FakeProvider(history_by_ticker={"AAPL": [_make_bar(date(2026, 8, 18))]}, failing_tickers=set())

    with patch("stockmon.services.refresh_service.upsert_daily_prices") as mock_upsert:
        failure = refresh_stock(db, provider, ticker, days=60)

    assert failure is None
    mock_upsert.assert_called_once_with(db, ticker.id, provider.fetch_daily_history("AAPL", 60))
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_refresh_stock_failure_returns_failure_and_rolls_back() -> None:
    ticker = Ticker(id=2, ticker="KO", company_name="Coca-Cola Co.")
    db = MagicMock()
    provider = FakeProvider(history_by_ticker={}, failing_tickers={"KO"})

    failure = refresh_stock(db, provider, ticker, days=60)

    assert failure is not None
    assert failure.ticker == "KO"
    assert failure.error == "download timeout for KO"
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_refresh_stock_overlays_live_quote_for_todays_bar() -> None:
    today_bar = _make_bar(date.today())
    ticker = Ticker(id=1, ticker="AAPL", company_name="Apple Inc.")
    db = MagicMock()
    quote = Quote(price=Decimal("12.34"), as_of=datetime.now())
    provider = FakeProvider(
        history_by_ticker={"AAPL": [today_bar]},
        failing_tickers=set(),
        quote_by_ticker={"AAPL": quote},
    )

    with patch("stockmon.services.refresh_service.upsert_daily_prices") as mock_upsert:
        failure = refresh_stock(db, provider, ticker, days=60)

    assert failure is None
    upserted_bars = mock_upsert.call_args.args[2]
    assert upserted_bars[-1].close == Decimal("12.34")
    assert provider.quote_calls == ["AAPL"]


def test_refresh_stock_falls_back_when_quote_fetch_fails() -> None:
    today_bar = _make_bar(date.today())
    ticker = Ticker(id=1, ticker="AAPL", company_name="Apple Inc.")
    db = MagicMock()
    provider = FakeProvider(
        history_by_ticker={"AAPL": [today_bar]},
        failing_tickers=set(),
        failing_quote_tickers={"AAPL"},
    )

    with patch("stockmon.services.refresh_service.upsert_daily_prices") as mock_upsert:
        failure = refresh_stock(db, provider, ticker, days=60)

    assert failure is None
    upserted_bars = mock_upsert.call_args.args[2]
    assert upserted_bars[-1].close == today_bar.close
    db.commit.assert_called_once()


def test_refresh_stock_does_not_fetch_quote_for_non_today_bar() -> None:
    ticker = Ticker(id=1, ticker="AAPL", company_name="Apple Inc.")
    db = MagicMock()
    provider = FakeProvider(
        history_by_ticker={"AAPL": [_make_bar(date(2026, 8, 18))]},
        failing_tickers=set(),
    )

    with patch("stockmon.services.refresh_service.upsert_daily_prices"):
        failure = refresh_stock(db, provider, ticker, days=60)

    assert failure is None
    assert provider.quote_calls == []
