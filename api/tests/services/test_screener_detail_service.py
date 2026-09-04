from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.services.screener_detail_service import get_screener_stock_detail
from stockmon.services.stock_service import UnknownTickerError


class FakeProvider(MarketDataProvider):
    def __init__(
        self,
        history_by_ticker: dict[str, list[DailyBar]],
        failing_history_tickers: set[str] | None = None,
        failing_name_tickers: set[str] | None = None,
        exchange_by_ticker: dict[str, str] | None = None,
        quote_by_ticker: dict[str, Quote] | None = None,
        failing_quote_tickers: set[str] | None = None,
    ):
        self._history_by_ticker = history_by_ticker
        self._failing_history_tickers = failing_history_tickers or set()
        self._failing_name_tickers = failing_name_tickers or set()
        self._exchange_by_ticker = exchange_by_ticker or {}
        self._quote_by_ticker = quote_by_ticker or {}
        self._failing_quote_tickers = failing_quote_tickers or set()
        self.quote_calls: list[str] = []

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if ticker in self._failing_history_tickers:
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
        if ticker in self._failing_name_tickers:
            raise MarketDataError(f"no name for {ticker}")
        return f"{ticker} Inc."

    def fetch_exchange(self, ticker: str) -> str | None:
        return self._exchange_by_ticker.get(ticker)


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


def test_valid_ticker_returns_full_unowned_detail() -> None:
    provider = FakeProvider(history_by_ticker={"PLTR": _bars(30)})

    detail = get_screener_stock_detail(provider, "pltr")

    assert detail.evaluation.ticker.ticker == "PLTR"
    assert detail.evaluation.ticker.company_name == "PLTR Inc."
    assert detail.evaluation.status == "ok"
    assert detail.evaluation.suggestion is not None
    assert detail.evaluation.suggestion.type == "entry"
    assert detail.evaluation.position is None
    assert detail.evaluation.position_value is None
    assert detail.user_avg_purchase_price is None
    assert detail.profit_target is None
    assert detail.chart_days is not None
    assert len(detail.chart_days) == 30
    assert detail.news_links.investor_relations is None


def test_overlays_live_quote_for_todays_bar() -> None:
    bars = _bars(30, start=date.today() - timedelta(days=29))
    quote = Quote(price=Decimal("55.10"), as_of=datetime.now())
    provider = FakeProvider(history_by_ticker={"PLTR": bars}, quote_by_ticker={"PLTR": quote})

    detail = get_screener_stock_detail(provider, "pltr")

    assert detail.evaluation.current_price == Decimal("55.10")
    assert provider.quote_calls == ["PLTR"]


def test_falls_back_when_quote_fetch_fails() -> None:
    bars = _bars(30, start=date.today() - timedelta(days=29))
    provider = FakeProvider(history_by_ticker={"PLTR": bars}, failing_quote_tickers={"PLTR"})

    detail = get_screener_stock_detail(provider, "pltr")

    assert detail.evaluation.current_price == Decimal(100)


def test_unknown_ticker_raises_unknown_ticker_error() -> None:
    provider = FakeProvider(history_by_ticker={}, failing_name_tickers={"ZZZZ"})

    with pytest.raises(UnknownTickerError):
        get_screener_stock_detail(provider, "ZZZZ")


def test_google_finance_link_uses_live_exchange_lookup() -> None:
    provider = FakeProvider(history_by_ticker={"PLTR": _bars(30)}, exchange_by_ticker={"PLTR": "NASDAQ"})

    detail = get_screener_stock_detail(provider, "pltr")

    assert detail.news_links.google_finance == "https://www.google.com/finance/quote/PLTR:NASDAQ"


def test_google_finance_link_omits_suffix_when_exchange_unresolved() -> None:
    provider = FakeProvider(history_by_ticker={"PLTR": _bars(30)})

    detail = get_screener_stock_detail(provider, "pltr")

    assert detail.news_links.google_finance == "https://www.google.com/finance/quote/PLTR"


def test_short_history_is_insufficient_history_not_an_error() -> None:
    provider = FakeProvider(history_by_ticker={"NEWCO": _bars(14)})

    detail = get_screener_stock_detail(provider, "NEWCO")

    assert detail.evaluation.status == "insufficient_history"
    assert detail.evaluation.suggestion is None
    assert detail.chart_days is None
    assert detail.trading_days_until_ready == 16


def test_history_fetch_failure_is_insufficient_history_not_an_error() -> None:
    provider = FakeProvider(history_by_ticker={}, failing_history_tickers={"NEWCO"})

    detail = get_screener_stock_detail(provider, "NEWCO")

    assert detail.evaluation.status == "insufficient_history"
    assert detail.evaluation.days_available == 0
    assert detail.evaluation.current_price is None
    assert detail.trading_days_until_ready == 30
