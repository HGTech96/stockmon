from datetime import date, timedelta
from decimal import Decimal

import pytest

from stockmon.db.models import CashEvent
from stockmon.services.cash_service import (
    CashNotFoundError,
    CashValidationError,
    delete_cash_event,
    list_cash_events,
    record_cash_event,
)
from stockmon.services.trade_service import record_trade
from tests.conftest import make_stock, make_user


def test_deposit_increases_cash_available(db) -> None:
    user = make_user(db)
    row, cash_available = record_cash_event(db, user.id, "deposit", Decimal(100), date(2026, 1, 1))

    assert row.id is not None
    assert cash_available == Decimal(100)


def test_withdraw_decreases_cash_available(db) -> None:
    user = make_user(db)
    record_cash_event(db, user.id, "deposit", Decimal(100), date(2026, 1, 1))

    _, cash_available = record_cash_event(db, user.id, "withdraw", Decimal(30), date(2026, 1, 2))

    assert cash_available == Decimal(70)


def test_withdraw_exceeding_cash_rejected(db) -> None:
    user = make_user(db)
    record_cash_event(db, user.id, "deposit", Decimal(100), date(2026, 1, 1))

    with pytest.raises(CashValidationError, match="Can't withdraw more than your available cash."):
        record_cash_event(db, user.id, "withdraw", Decimal(150), date(2026, 1, 2))


def test_amount_must_be_positive(db) -> None:
    user = make_user(db)
    with pytest.raises(CashValidationError, match="Amount must be greater than 0"):
        record_cash_event(db, user.id, "deposit", Decimal(0), date(2026, 1, 1))


def test_future_date_rejected(db) -> None:
    user = make_user(db)
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(CashValidationError, match="cannot be in the future"):
        record_cash_event(db, user.id, "deposit", Decimal(10), tomorrow)


def test_deposit_a_buy_depends_on_cannot_be_deleted(db) -> None:
    user = make_user(db)
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    deposit, _ = record_cash_event(db, user.id, "deposit", Decimal(1000), date(2026, 1, 1))
    record_trade(db, user.id, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 2))

    with pytest.raises(CashValidationError, match="a later buy or withdrawal depends on it"):
        delete_cash_event(db, user.id, deposit.id)

    assert db.get(CashEvent, deposit.id) is not None


def test_deposit_with_no_dependents_can_be_deleted(db) -> None:
    user = make_user(db)
    deposit, _ = record_cash_event(db, user.id, "deposit", Decimal(1000), date(2026, 1, 1))

    cash_available = delete_cash_event(db, user.id, deposit.id)

    assert cash_available == Decimal(0)
    assert db.get(CashEvent, deposit.id) is None


def test_delete_not_found_raises(db) -> None:
    user = make_user(db)
    with pytest.raises(CashNotFoundError):
        delete_cash_event(db, user.id, 999)


def test_delete_of_another_users_event_raises_not_found(db) -> None:
    owner = make_user(db, username="owner")
    other = make_user(db, username="other")
    deposit, _ = record_cash_event(db, owner.id, "deposit", Decimal(1000), date(2026, 1, 1))

    with pytest.raises(CashNotFoundError):
        delete_cash_event(db, other.id, deposit.id)


def test_list_cash_events_newest_first_with_cash_available(db) -> None:
    user = make_user(db)
    record_cash_event(db, user.id, "deposit", Decimal(100), date(2026, 1, 1))
    record_cash_event(db, user.id, "withdraw", Decimal(20), date(2026, 1, 5))

    entries, cash_available = list_cash_events(db, user.id)

    assert [(e.type, e.date) for e in entries] == [("withdraw", date(2026, 1, 5)), ("deposit", date(2026, 1, 1))]
    assert cash_available == Decimal(80)


def test_list_cash_events_empty(db) -> None:
    user = make_user(db)
    entries, cash_available = list_cash_events(db, user.id)
    assert entries == []
    assert cash_available == Decimal(0)


def test_list_cash_events_only_shows_this_users_events(db) -> None:
    user = make_user(db, username="user")
    other = make_user(db, username="other")
    record_cash_event(db, user.id, "deposit", Decimal(100), date(2026, 1, 1))
    record_cash_event(db, other.id, "deposit", Decimal(500), date(2026, 1, 1))

    entries, cash_available = list_cash_events(db, user.id)

    assert len(entries) == 1
    assert cash_available == Decimal(100)


def test_deposit_and_buy_same_day_never_rejected(db) -> None:
    """Money-in-before-money-out same-day tie-break, exercised end to end:
    depositing exactly enough and buying with it the same day must succeed."""
    user = make_user(db)
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    record_cash_event(db, user.id, "deposit", Decimal(1000), date(2026, 1, 1))

    result = record_trade(db, user.id, "AAPL", "buy", Decimal(10), Decimal(100), date(2026, 1, 1))

    assert result.updated_position is not None
