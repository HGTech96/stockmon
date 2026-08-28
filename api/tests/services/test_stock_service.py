from datetime import date
from decimal import Decimal

import pytest

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.core.position import TradeEvent, derive_position
from stockmon.db.models import DailyPrice, Stock, Trade
from stockmon.services.stock_service import (
    StockAlreadyOnWatchlistError,
    StockNotFoundError,
    UnknownTickerError,
    add_stock_to_watchlist,
    clear_analysis,
    evaluate_stock_snapshot,
    set_analysis,
)
from tests.conftest import make_daily_prices, make_stock

TARGET = Decimal("50.00")


class FakeProvider(MarketDataProvider):
    """Test double resolving one ticker to a name + optional history,
    matching the MarketDataProvider ABC exactly (fetch_company_name
    included) so it can stand in for a real provider in add_stock tests."""

    def __init__(self, company_name: str | None, bars: list[DailyBar] | None = None, exchange: str | None = None):
        self._company_name = company_name
        self._bars = bars
        self._exchange = exchange

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if self._bars is None:
            raise MarketDataError(f"no price history returned for {ticker}")
        return self._bars

    def fetch_current_quote(self, ticker: str) -> Quote:
        raise NotImplementedError

    def fetch_company_name(self, ticker: str) -> str:
        if self._company_name is None:
            raise MarketDataError(f"no company name available for {ticker}")
        return self._company_name

    def fetch_exchange(self, ticker: str) -> str | None:
        return self._exchange


def _make_bar() -> DailyBar:
    return DailyBar(
        date=date(2026, 8, 18),
        open=Decimal("10.00"),
        high=Decimal("11.00"),
        low=Decimal("9.00"),
        close=Decimal("10.50"),
        volume=1000,
    )


def test_ok_status_with_thirty_bars_and_no_position(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["90.00"])

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "ok"
    assert evaluation.indicators is not None
    assert evaluation.current_price == Decimal("90.00")
    assert evaluation.position is None
    assert evaluation.position_value is None
    assert evaluation.suggestion is not None
    assert evaluation.suggestion.type == "entry"


def test_insufficient_history_falls_back_to_price_snapshot(db) -> None:
    stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.")
    make_daily_prices(db, stock, ["12.00", "13.42"])

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "insufficient_history"
    assert evaluation.indicators is None
    assert evaluation.suggestion is None
    assert evaluation.warning is None
    assert evaluation.current_price == Decimal("13.42")
    assert evaluation.days_available == 2


def test_never_refreshed_has_no_current_price(db) -> None:
    stock = make_stock(db, "NEW", "Newly Added Inc.")

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "insufficient_history"
    assert evaluation.current_price is None
    assert evaluation.days_available == 0


def test_owned_stock_computes_position_value_when_ok(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["120.00"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)))
    db.commit()

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.position is not None
    assert evaluation.position_value is not None
    assert evaluation.position_value.profit_loss == Decimal(200)
    assert evaluation.suggestion is not None


def test_owned_stock_insufficient_history_still_has_position_value(db) -> None:
    stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.")
    make_daily_prices(db, stock, ["12.00", "13.00"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(5), price_per_share=Decimal(10), trade_date=date(2026, 1, 1)))
    db.commit()

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "insufficient_history"
    assert evaluation.position is not None
    assert evaluation.position_value is not None
    assert evaluation.position_value.current_value == Decimal(65)
    assert evaluation.suggestion is None


def test_trade_events_loaded_in_chronological_order(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 30)
    db.add_all(
        [
            Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 5)),
            Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(120), trade_date=date(2026, 1, 1)),
        ]
    )
    db.commit()

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    expected = derive_position(
        [
            TradeEvent(action="buy", shares=Decimal(10), price_per_share=Decimal(120), date=date(2026, 1, 1)),
            TradeEvent(action="buy", shares=Decimal(10), price_per_share=Decimal(100), date=date(2026, 1, 5)),
        ]
    )
    assert evaluation.position == expected


def test_add_stock_valid_ticker_stores_name_and_history(db) -> None:
    provider = FakeProvider(company_name="Palantir Technologies Inc.", bars=[_make_bar()])

    result = add_stock_to_watchlist(db, provider, "pltr")

    assert result.history_fetched is True
    assert result.stock.ticker == "PLTR"  # uppercased server-side
    assert result.stock.company_name == "Palantir Technologies Inc."

    stored = db.query(Stock).filter(Stock.ticker == "PLTR").first()
    assert stored is not None
    assert len(_load_bars_for(db, stored)) == 1


def test_add_stock_stores_exchange_from_provider(db) -> None:
    provider = FakeProvider(company_name="Palantir Technologies Inc.", bars=[_make_bar()], exchange="NASDAQ")

    add_stock_to_watchlist(db, provider, "pltr")

    stored = db.query(Stock).filter(Stock.ticker == "PLTR").first()
    assert stored.exchange == "NASDAQ"


def test_add_stock_unresolved_exchange_stores_none(db) -> None:
    provider = FakeProvider(company_name="Palantir Technologies Inc.", bars=[_make_bar()], exchange=None)

    add_stock_to_watchlist(db, provider, "pltr")

    stored = db.query(Stock).filter(Stock.ticker == "PLTR").first()
    assert stored.exchange is None


def test_add_stock_name_resolves_but_history_fetch_fails_still_adds(db) -> None:
    provider = FakeProvider(company_name="New Listing Inc.", bars=None)

    result = add_stock_to_watchlist(db, provider, "NEWCO")

    assert result.history_fetched is False
    assert db.query(Stock).filter(Stock.ticker == "NEWCO").first() is not None


def test_add_stock_unknown_ticker_raises_and_stores_nothing(db) -> None:
    provider = FakeProvider(company_name=None)

    with pytest.raises(UnknownTickerError):
        add_stock_to_watchlist(db, provider, "ZZZZ")

    assert db.query(Stock).filter(Stock.ticker == "ZZZZ").first() is None


def test_add_stock_blank_company_name_is_treated_as_unresolved(db) -> None:
    provider = FakeProvider(company_name="   ")

    with pytest.raises(UnknownTickerError):
        add_stock_to_watchlist(db, provider, "ZZZZ")


def test_add_stock_already_on_watchlist_raises_409(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    provider = FakeProvider(company_name="Apple Inc.", bars=[_make_bar()])

    with pytest.raises(StockAlreadyOnWatchlistError):
        add_stock_to_watchlist(db, provider, "AAPL")


def test_add_stock_duplicate_check_is_case_insensitive(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    provider = FakeProvider(company_name="Apple Inc.", bars=[_make_bar()])

    with pytest.raises(StockAlreadyOnWatchlistError):
        add_stock_to_watchlist(db, provider, "aapl")


def _load_bars_for(db, stock) -> list:
    return db.query(DailyPrice).filter(DailyPrice.stock_id == stock.id).all()


def test_set_analysis_stores_date_and_value(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    view = set_analysis(db, "AAPL", date(2026, 8, 20), Decimal("210.00"))

    assert view.date == date(2026, 8, 20)
    assert view.value == Decimal("210.00")
    stored = db.query(Stock).filter(Stock.ticker == "AAPL").first()
    assert stored.analysis_date == date(2026, 8, 20)
    assert stored.analysis_value == Decimal("210.00")


def test_set_analysis_overwrites_existing_value(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    set_analysis(db, "AAPL", date(2026, 8, 20), Decimal("210.00"))

    view = set_analysis(db, "AAPL", date(2026, 8, 25), Decimal("225.50"))

    assert view.date == date(2026, 8, 25)
    assert view.value == Decimal("225.50")


def test_set_analysis_unknown_ticker_raises(db) -> None:
    with pytest.raises(StockNotFoundError):
        set_analysis(db, "ZZZZ", date(2026, 8, 20), Decimal("210.00"))


def test_clear_analysis_resets_to_null(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    set_analysis(db, "AAPL", date(2026, 8, 20), Decimal("210.00"))

    clear_analysis(db, "AAPL")

    stored = db.query(Stock).filter(Stock.ticker == "AAPL").first()
    assert stored.analysis_date is None
    assert stored.analysis_value is None


def test_clear_analysis_with_no_existing_value_is_a_no_op(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    clear_analysis(db, "AAPL")  # should not raise

    stored = db.query(Stock).filter(Stock.ticker == "AAPL").first()
    assert stored.analysis_date is None


def test_clear_analysis_unknown_ticker_raises(db) -> None:
    with pytest.raises(StockNotFoundError):
        clear_analysis(db, "ZZZZ")
