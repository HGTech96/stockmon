from datetime import date
from decimal import Decimal

from stockmon.services.cash_service import record_cash_event
from stockmon.services.money_service import build_money_summary, has_money_activity
from stockmon.services.trade_service import record_trade
from tests.conftest import make_stock, make_user


def test_no_activity_is_false(db) -> None:
    user = make_user(db)
    assert has_money_activity(db, user.id) is False


def test_a_trade_alone_counts_as_activity(db) -> None:
    user = make_user(db)
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    record_cash_event(db, user.id, "deposit", Decimal(1000), date(2026, 1, 1))
    record_trade(db, user.id, "AAPL", "buy", Decimal(1), Decimal(10), date(2026, 1, 1))

    assert has_money_activity(db, user.id) is True


def test_a_deposit_alone_with_zero_trades_counts_as_activity(db) -> None:
    """A deposit with no trades yet is a valid, important state -- money must
    render even though there's no position/summary to show."""
    user = make_user(db)
    record_cash_event(db, user.id, "deposit", Decimal(100), date(2026, 1, 1))

    assert has_money_activity(db, user.id) is True


def test_deposit_buy_sell_buy_recycling_keeps_net_deposited_flat(db) -> None:
    """netDeposited reflects only external money in/out; cashAvailable moves
    with recycled sale proceeds being spent again."""
    user = make_user(db)
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    record_cash_event(db, user.id, "deposit", Decimal(1000), date(2026, 1, 1))
    record_trade(db, user.id, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 2))  # spend 1000, cash 0
    record_trade(db, user.id, "AAPL", "sell", Decimal(10), Decimal(120), date(2026, 1, 3))  # +1200, cash 1200
    record_trade(db, user.id, "AAPL", "buy", Decimal(10), Decimal(110), date(2026, 1, 4))  # spend 1100, cash 100

    summary = build_money_summary(db, user.id, open_position_pnls=[Decimal(0)])

    assert summary.net_deposited == Decimal(1000)
    assert summary.cash_available == Decimal(100)
    assert summary.realized_earned == Decimal(200)


def test_build_money_summary_uses_realized_pnl_from_trade_history(db) -> None:
    user = make_user(db)
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    record_cash_event(db, user.id, "deposit", Decimal(1000), date(2026, 1, 1))
    record_trade(db, user.id, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 2))
    record_trade(db, user.id, "AAPL", "sell", Decimal(4), Decimal(150), date(2026, 1, 3))

    summary = build_money_summary(db, user.id, open_position_pnls=[])

    assert summary.realized_earned == Decimal(200)
    assert summary.realized_lost == Decimal(0)
