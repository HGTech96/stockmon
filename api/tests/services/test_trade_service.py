from datetime import date, timedelta
from decimal import Decimal

import pytest

from stockmon.db.models import Trade
from stockmon.services.cash_service import record_cash_event
from stockmon.services.trade_service import (
    TradeNotFoundError,
    TradeValidationError,
    delete_trade,
    list_trade_history,
    record_trade,
    update_trade,
)
from tests.conftest import make_deposit, make_stock


def test_buy_opens_new_position(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)

    result = record_trade(db, "AAPL", "buy", Decimal(5), Decimal("189.10"), date(2026, 8, 19))

    assert result.trade.id is not None
    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(5)
    assert result.updated_position.avg_purchase_price == Decimal("189.10")


def test_buy_then_buy_recomputes_weighted_average(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))

    result = record_trade(db, "AAPL", "buy", Decimal(5), Decimal(189), date(2026, 8, 19))

    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(15)
    assert result.updated_position.amount_invested == Decimal(10 * 100 + 5 * 189)


def test_sell_that_closes_position_returns_none(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))

    result = record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 10))

    assert result.updated_position is None


def test_partial_sell_keeps_avg_price(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
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
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(5), Decimal(100), date(2026, 1, 1))
    with pytest.raises(TradeValidationError, match="only 5"):
        record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 10))


def test_backdated_buy_recomputes_from_full_history(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
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
    make_deposit(db)
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
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))
    record_trade(db, "AAPL", "sell", Decimal(4), Decimal(150), date(2026, 1, 10))

    entries = list_trade_history(db)
    sell, buy = entries

    assert sell.company_name == "Apple Inc."
    assert sell.total_usd == Decimal(600)
    assert sell.realized_pnl_usd == Decimal(200)
    assert buy.total_usd == Decimal(1000)
    assert buy.realized_pnl_usd is None


def test_update_trade_recalculates_position(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    buy = record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1)).trade
    record_trade(db, "AAPL", "sell", Decimal(4), Decimal(150), date(2026, 1, 10))

    result = update_trade(db, buy.id, Decimal(20), Decimal(100), date(2026, 1, 1))

    assert result.trade.shares == Decimal(20)
    assert result.updated_position is not None
    assert result.updated_position.shares_held == Decimal(16)


def test_update_trade_not_found_raises(db) -> None:
    with pytest.raises(TradeNotFoundError):
        update_trade(db, 999, Decimal(1), Decimal(10), date(2026, 1, 1))


def test_update_trade_oversell_rejected_and_db_unchanged(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    buy = record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1)).trade
    record_trade(db, "AAPL", "sell", Decimal(8), Decimal(150), date(2026, 1, 10))

    with pytest.raises(TradeValidationError):
        update_trade(db, buy.id, Decimal(5), Decimal(100), date(2026, 1, 1))

    unchanged = db.query(Trade).filter(Trade.id == buy.id).first()
    assert unchanged.shares == Decimal(10)


def test_update_trade_invalid_field_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    buy = record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1)).trade

    with pytest.raises(TradeValidationError, match="Shares must be greater than 0"):
        update_trade(db, buy.id, Decimal(0), Decimal(100), date(2026, 1, 1))


def test_delete_trade_recalculates_position(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))
    second_buy = record_trade(db, "AAPL", "buy", Decimal(5), Decimal(120), date(2026, 1, 5)).trade

    position = delete_trade(db, second_buy.id)

    assert position is not None
    assert position.shares_held == Decimal(10)
    assert db.query(Trade).filter(Trade.id == second_buy.id).first() is None


def test_delete_trade_leaving_no_shares_returns_none(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))
    sell = record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 10)).trade
    reopen = record_trade(db, "AAPL", "buy", Decimal(5), Decimal(200), date(2026, 1, 20)).trade

    position = delete_trade(db, reopen.id)

    assert position is None
    assert sell.id is not None


def test_delete_trade_not_found_raises(db) -> None:
    with pytest.raises(TradeNotFoundError):
        delete_trade(db, 999)


def test_delete_trade_oversell_rejected_and_db_unchanged(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_deposit(db)
    record_trade(db, "AAPL", "buy", Decimal(5), Decimal(100), date(2026, 1, 1))
    second_buy = record_trade(db, "AAPL", "buy", Decimal(5), Decimal(100), date(2026, 1, 5)).trade
    record_trade(db, "AAPL", "sell", Decimal(8), Decimal(150), date(2026, 1, 10))

    with pytest.raises(TradeValidationError):
        delete_trade(db, second_buy.id)

    assert db.query(Trade).filter(Trade.id == second_buy.id).first() is not None


def test_fractional_buy_draws_exact_cash_amount(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_cash_event(db, "deposit", Decimal("200.00"), date(2026, 1, 1))

    # 1.256789 shares * 150.25 = exactly 188.83254725 -- leaves 11.16745275
    # available (Decimal-exact, not rounded to cents). A buy needing one
    # cent more must be rejected; a buy within the remaining balance must
    # still succeed.
    record_trade(db, "AAPL", "buy", Decimal("1.256789"), Decimal("150.25"), date(2026, 1, 2))

    with pytest.raises(TradeValidationError, match="Insufficient cash"):
        record_trade(db, "AAPL", "buy", Decimal("0.075"), Decimal("150.25"), date(2026, 1, 3))

    # 0.074325 * 150.25 = 11.16733125, just inside the 11.16745275 remaining
    record_trade(db, "AAPL", "buy", Decimal("0.074325"), Decimal("150.25"), date(2026, 1, 4))


def test_buy_exceeding_cash_rejected_and_not_inserted(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_cash_event(db, "deposit", Decimal(500), date(2026, 1, 1))

    with pytest.raises(TradeValidationError, match="Insufficient cash — record a deposit first."):
        record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 2))

    assert db.query(Trade).count() == 0


def test_update_trade_shrinking_a_sell_that_strands_a_later_buy_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_cash_event(db, "deposit", Decimal(1000), date(2026, 1, 1))
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 2))  # cash 0
    sell = record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 3)).trade  # cash 1500
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(140), date(2026, 1, 4))  # relies on the 1500, cash 100

    with pytest.raises(TradeValidationError, match="Can't make this change — a later buy or withdrawal depends on it."):
        update_trade(db, sell.id, Decimal(1), Decimal(150), date(2026, 1, 3))

    unchanged = db.query(Trade).filter(Trade.id == sell.id).first()
    assert unchanged.shares == Decimal(10)


def test_delete_trade_removing_a_sell_that_strands_a_later_buy_rejected(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_cash_event(db, "deposit", Decimal(1000), date(2026, 1, 1))
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 2))  # cash 0
    sell = record_trade(db, "AAPL", "sell", Decimal(10), Decimal(150), date(2026, 1, 3)).trade  # cash 1500
    record_trade(db, "AAPL", "buy", Decimal(10), Decimal(140), date(2026, 1, 4))  # relies on the 1500, cash 100

    with pytest.raises(TradeValidationError, match="Can't remove this — a later buy or withdrawal depends on it."):
        delete_trade(db, sell.id)

    assert db.query(Trade).filter(Trade.id == sell.id).first() is not None
