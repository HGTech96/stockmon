from datetime import date, timedelta
from decimal import Decimal

import pytest

from stockmon.services.trade_service import TradeValidationError, list_trade_history, record_trade
from tests.conftest import make_stock


def test_buy_opens_new_position(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    result = record_trade(db, "AAPL", "buy", Decimal(5), Decimal("189.10"), date(2026, 8, 19))

    assert result.trade.id is not None
    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(5)
    assert result.updated_position.avg_purchase_price == Decimal("189.10")


def test_buy_then_buy_recomputes_weighted_average(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))

    result = record_trade(db, "AAPL", "buy", Decimal(5), Decimal(189), date(2026, 8, 19))

    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(15)
    assert result.updated_position.amount_invested == Decimal(10 * 100 + 5 * 189)


def test_sell_that_closes_position_returns_none(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))

    result = record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 10))

    assert result.updated_position is None


def test_partial_sell_keeps_avg_price(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))

    result = record_trade(db, "AAPL", "sell", Decimal(4), Decimal(150), date(2026, 1, 10))

    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(6)
    assert result.updated_position.avg_purchase_price == Decimal(100)


def test_unknown_ticker_rejected(db) -> None:
    with pytest.raises(TradeValidationError, match="not on the watchlist"):
        record_trade(db, "ZZZZ", "buy", Decimal(1), Decimal(10), date(2026, 1, 1))


def test_zero_shares_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    with pytest.raises(TradeValidationError, match="Shares must be greater than 0"):
        record_trade(db, "AAPL", "buy", Decimal(0), Decimal(10), date(2026, 1, 1))


def test_negative_price_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    with pytest.raises(TradeValidationError, match="Price per share must be greater than 0"):
        record_trade(db, "AAPL", "buy", Decimal(1), Decimal(-10), date(2026, 1, 1))


def test_future_date_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(TradeValidationError, match="cannot be in the future"):
        record_trade(db, "AAPL", "buy", Decimal(1), Decimal(10), tomorrow)


def test_sell_with_no_position_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    with pytest.raises(TradeValidationError, match="No open position"):
        record_trade(db, "AAPL", "sell", Decimal(1), Decimal(10), date(2026, 1, 1))


def test_oversell_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_trade(db, "AAPL", "buy", Decimal(5), Decimal(100), date(2026, 1, 1))
    with pytest.raises(TradeValidationError, match="only 5"):
        record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 10))


def test_backdated_buy_recomputes_from_full_history(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 5))

    result = record_trade(db, "AAPL", "buy", Decimal(10), Decimal(120), date(2026, 1, 1))

    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(20)
    assert result.updated_position.amount_invested == Decimal(10 * 120 + 10 * 100)


def test_list_trade_history_empty(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    assert list_trade_history(db) == []


def test_list_trade_history_ordered_newest_first_across_tickers(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_stock(db, "MSFT", "Microsoft Corporation")
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))
    record_trade(db, "MSFT", "buy", Decimal(5), Decimal(50), date(2026, 1, 2))
    record_trade(db, "AAPL", "sell", Decimal(4), Decimal(150), date(2026, 1, 3))

    entries = list_trade_history(db)

    assert [(e.ticker, e.action, e.date) for e in entries] == [
        ("AAPL", "sell", date(2026, 1, 3)),
        ("MSFT", "buy", date(2026, 1, 2)),
        ("AAPL", "buy", date(2026, 1, 1)),
    ]


def test_list_trade_history_totals_and_realized_pnl(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))
    record_trade(db, "AAPL", "sell", Decimal(4), Decimal(150), date(2026, 1, 10))

    entries = list_trade_history(db)
    sell, buy = entries

    assert sell.company_name == "Apple Inc."
    assert sell.total_usd == Decimal(600)
    assert sell.realized_pnl_usd == Decimal(200)
    assert buy.total_usd == Decimal(1000)
    assert buy.realized_pnl_usd is None
