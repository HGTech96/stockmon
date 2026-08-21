from datetime import date
from decimal import Decimal

import pytest

from stockmon.core.cash import CashError, CashFlowEvent, chronological_key, derive_cash_balance


def _deposit(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="deposit", amount=Decimal(amount), date=day)


def _withdraw(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="withdraw", amount=Decimal(amount), date=day)


def _buy(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="buy", amount=Decimal(amount), date=day)


def _sell(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="sell", amount=Decimal(amount), date=day)


def test_deposit_then_buy_ok() -> None:
    events = sorted(
        [_deposit("100", date(2026, 1, 1)), _buy("60", date(2026, 1, 1))], key=chronological_key
    )
    assert derive_cash_balance(events) == Decimal(40)


def test_same_day_deposit_and_buy_never_rejected_regardless_of_input_order() -> None:
    """Same-day money-in-before-money-out tie-break: this must hold whichever
    order the caller happened to construct the (unsorted) input list in --
    the sort key, not caller ordering, decides."""
    day = date(2026, 1, 1)
    forward = [_deposit("100", day), _buy("100", day)]
    reversed_input = [_buy("100", day), _deposit("100", day)]

    assert derive_cash_balance(sorted(forward, key=chronological_key)) == Decimal(0)
    assert derive_cash_balance(sorted(reversed_input, key=chronological_key)) == Decimal(0)


def test_same_day_sell_and_withdraw_never_rejected() -> None:
    day = date(2026, 1, 1)
    events = sorted(
        [_deposit("100", date(2025, 12, 1)), _buy("100", date(2025, 12, 1)), _sell("50", day), _withdraw("50", day)],
        key=chronological_key,
    )
    assert derive_cash_balance(events) == Decimal(0)


def test_withdraw_exceeding_balance_raises() -> None:
    events = sorted(
        [_deposit("100", date(2026, 1, 1)), _withdraw("150", date(2026, 1, 2))], key=chronological_key
    )
    with pytest.raises(CashError):
        derive_cash_balance(events)


def test_buy_exceeding_balance_raises() -> None:
    events = sorted([_deposit("100", date(2026, 1, 1)), _buy("150", date(2026, 1, 2))], key=chronological_key)
    with pytest.raises(CashError):
        derive_cash_balance(events)


def test_backdated_withdraw_that_would_go_negative_at_its_point_raises() -> None:
    """Even though the FINAL balance is non-negative, a backdated withdrawal
    landing before the deposit that would have covered it must still reject
    -- the replay checks every point, not just the end state."""
    events = sorted(
        [_deposit("100", date(2026, 1, 10)), _withdraw("50", date(2026, 1, 1))], key=chronological_key
    )
    with pytest.raises(CashError):
        derive_cash_balance(events)


def test_non_strict_never_raises_and_reports_the_true_negative_balance() -> None:
    events = sorted([_withdraw("50", date(2026, 1, 1))], key=chronological_key)
    assert derive_cash_balance(events, strict=False) == Decimal(-50)
