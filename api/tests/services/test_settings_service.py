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
from tests.conftest import make_stock


def test_get_settings_creates_default_row_when_absent(db) -> None:
    view = get_settings(db)
    assert view.default_profit_target_dollars == DEFAULT_TARGET
    assert view.per_position_targets == {}


def test_update_default_target(db) -> None:
    view = update_default_target(db, Decimal("75.00"))
    assert view.default_profit_target_dollars == Decimal("75.00")
    assert get_settings(db).default_profit_target_dollars == Decimal("75.00")


def test_set_position_target_creates_override(db) -> None:
    stock = make_stock(db, "AAPL")
    view = set_position_target(db, "AAPL", Decimal("150.00"))
    assert view.per_position_targets == {"AAPL": Decimal("150.00")}
    assert get_effective_target(db, stock.id) == Decimal("150.00")


def test_set_position_target_updates_existing_override(db) -> None:
    make_stock(db, "AAPL")
    set_position_target(db, "AAPL", Decimal("150.00"))
    view = set_position_target(db, "AAPL", Decimal("200.00"))
    assert view.per_position_targets == {"AAPL": Decimal("200.00")}


def test_set_position_target_unknown_ticker_raises_not_found(db) -> None:
    with pytest.raises(StockNotFoundError):
        set_position_target(db, "ZZZZ", Decimal("100.00"))


def test_effective_target_falls_back_to_default_without_override(db) -> None:
    stock = make_stock(db, "AAPL")
    update_default_target(db, Decimal("60.00"))
    assert get_effective_target(db, stock.id) == Decimal("60.00")


def test_remove_position_target_clears_override(db) -> None:
    stock = make_stock(db, "AAPL")
    set_position_target(db, "AAPL", Decimal("150.00"))
    update_default_target(db, Decimal("60.00"))

    view = remove_position_target(db, "AAPL")

    assert view.per_position_targets == {}
    assert get_effective_target(db, stock.id) == Decimal("60.00")


def test_remove_position_target_is_noop_without_existing_override(db) -> None:
    make_stock(db, "AAPL")
    view = remove_position_target(db, "AAPL")
    assert view.per_position_targets == {}


def test_remove_position_target_unknown_ticker_raises_not_found(db) -> None:
    with pytest.raises(StockNotFoundError):
        remove_position_target(db, "ZZZZ")
