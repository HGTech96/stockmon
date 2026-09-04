from decimal import Decimal

import pytest

from stockmon.services.settings_service import (
    DEFAULT_TARGET,
    get_effective_target,
    get_settings,
    remove_position_target,
    set_position_target,
    update_default_target,
)
from stockmon.services.stock_service import StockNotFoundError
from tests.conftest import make_stock, make_user


def test_get_settings_creates_default_row_when_absent(db) -> None:
    user = make_user(db)
    view = get_settings(db, user.id)
    assert view.default_profit_target_dollars == DEFAULT_TARGET
    assert view.per_position_targets == {}


def test_update_default_target(db) -> None:
    user = make_user(db)
    view = update_default_target(db, user.id, Decimal("75.00"))
    assert view.default_profit_target_dollars == Decimal("75.00")
    assert get_settings(db, user.id).default_profit_target_dollars == Decimal("75.00")


def test_set_position_target_creates_override(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "AAPL", user=user)
    view = set_position_target(db, user.id, "AAPL", Decimal("150.00"))
    assert view.per_position_targets == {"AAPL": Decimal("150.00")}
    assert get_effective_target(db, stock.id) == Decimal("150.00")


def test_set_position_target_updates_existing_override(db) -> None:
    user = make_user(db)
    make_stock(db, "AAPL", user=user)
    set_position_target(db, user.id, "AAPL", Decimal("150.00"))
    view = set_position_target(db, user.id, "AAPL", Decimal("200.00"))
    assert view.per_position_targets == {"AAPL": Decimal("200.00")}


def test_set_position_target_unknown_ticker_raises_not_found(db) -> None:
    user = make_user(db)
    with pytest.raises(StockNotFoundError):
        set_position_target(db, user.id, "ZZZZ", Decimal("100.00"))


def test_effective_target_falls_back_to_default_without_override(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "AAPL", user=user)
    update_default_target(db, user.id, Decimal("60.00"))
    assert get_effective_target(db, stock.id) == Decimal("60.00")


def test_remove_position_target_clears_override(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "AAPL", user=user)
    set_position_target(db, user.id, "AAPL", Decimal("150.00"))
    update_default_target(db, user.id, Decimal("60.00"))

    view = remove_position_target(db, user.id, "AAPL")

    assert view.per_position_targets == {}
    assert get_effective_target(db, stock.id) == Decimal("60.00")


def test_remove_position_target_is_noop_without_existing_override(db) -> None:
    user = make_user(db)
    make_stock(db, "AAPL", user=user)
    view = remove_position_target(db, user.id, "AAPL")
    assert view.per_position_targets == {}


def test_remove_position_target_unknown_ticker_raises_not_found(db) -> None:
    user = make_user(db)
    with pytest.raises(StockNotFoundError):
        remove_position_target(db, user.id, "ZZZZ")


def test_settings_are_isolated_per_user(db) -> None:
    user = make_user(db, username="user")
    other = make_user(db, username="other")
    update_default_target(db, user.id, Decimal("75.00"))

    assert get_settings(db, other.id).default_profit_target_dollars == DEFAULT_TARGET


def test_set_position_target_cannot_target_another_users_stock(db) -> None:
    owner = make_user(db, username="owner")
    other = make_user(db, username="other")
    make_stock(db, "AAPL", user=owner)

    with pytest.raises(StockNotFoundError):
        set_position_target(db, other.id, "AAPL", Decimal("150.00"))
