from datetime import date
from decimal import Decimal

import pytest

from stockmon.core.position import (
    Position,
    PositionError,
    ProfitTargetProgress,
    TradeEvent,
    compute_realized_pnl,
    derive_position,
    evaluate_profit_target,
    value_position,
)


def _buy(shares: str, price: str, day: date) -> TradeEvent:
    return TradeEvent(action="buy", shares=Decimal(shares), price_per_share=Decimal(price), date=day)


def _sell(shares: str, price: str, day: date) -> TradeEvent:
    return TradeEvent(action="sell", shares=Decimal(shares), price_per_share=Decimal(price), date=day)


def test_single_buy() -> None:
    trades = [_buy("10", "100.00", date(2026, 1, 1))]
    position = derive_position(trades)
    assert position == Position(
        shares_held=Decimal(10),
        avg_purchase_price=Decimal(100),
        amount_invested=Decimal(1000),
    )


def test_buy_then_buy_recomputes_weighted_average() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _buy("10", "120.00", date(2026, 1, 5)),
    ]
    position = derive_position(trades)
    assert position is not None
    assert position.shares_held == Decimal(20)
    assert position.amount_invested == Decimal(2200)
    assert position.avg_purchase_price == Decimal(110)


def test_buy_then_partial_sell_keeps_avg_price() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("4", "150.00", date(2026, 1, 10)),
    ]
    position = derive_position(trades)
    assert position is not None
    assert position.shares_held == Decimal(6)
    assert position.avg_purchase_price == Decimal(100)
    assert position.amount_invested == Decimal(600)


def test_buy_then_sell_all_closes_position() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("10", "150.00", date(2026, 1, 10)),
    ]
    assert derive_position(trades) is None


def test_reopen_after_close_resets_avg_price() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("10", "150.00", date(2026, 1, 10)),
        _buy("5", "200.00", date(2026, 2, 1)),
    ]
    position = derive_position(trades)
    assert position == Position(
        shares_held=Decimal(5),
        avg_purchase_price=Decimal(200),
        amount_invested=Decimal(1000),
    )


def test_oversell_raises_position_error() -> None:
    trades = [
        _buy("5", "100.00", date(2026, 1, 1)),
        _sell("10", "150.00", date(2026, 1, 10)),
    ]
    with pytest.raises(PositionError):
        derive_position(trades)


def test_sell_with_no_prior_position_raises() -> None:
    trades = [_sell("1", "150.00", date(2026, 1, 1))]
    with pytest.raises(PositionError):
        derive_position(trades)


def test_value_position_profit() -> None:
    position = Position(
        shares_held=Decimal(10), avg_purchase_price=Decimal(100), amount_invested=Decimal(1000)
    )
    value = value_position(position, current_price=Decimal("120.00"))
    assert value.current_value == Decimal(1200)
    assert value.profit_loss == Decimal(200)
    assert value.profit_loss_pct == Decimal(20)


def test_value_position_loss() -> None:
    position = Position(
        shares_held=Decimal(10), avg_purchase_price=Decimal(100), amount_invested=Decimal(1000)
    )
    value = value_position(position, current_price=Decimal("90.00"))
    assert value.current_value == Decimal(900)
    assert value.profit_loss == Decimal(-100)
    assert value.profit_loss_pct == Decimal(-10)


def test_profit_target_not_reached() -> None:
    progress = evaluate_profit_target(profit_loss=Decimal("30.00"), target_dollars=Decimal("50.00"))
    assert progress == ProfitTargetProgress(
        target_dollars=Decimal("50.00"),
        progress_dollars=Decimal("30.00"),
        remaining_dollars=Decimal("20.00"),
        reached=False,
    )


def test_profit_target_reached_exactly() -> None:
    progress = evaluate_profit_target(profit_loss=Decimal("50.00"), target_dollars=Decimal("50.00"))
    assert progress.reached is True
    assert progress.progress_dollars == Decimal("50.00")
    assert progress.remaining_dollars == Decimal(0)


def test_profit_target_progress_capped_above_target() -> None:
    progress = evaluate_profit_target(profit_loss=Decimal("150.00"), target_dollars=Decimal("50.00"))
    assert progress.reached is True
    assert progress.progress_dollars == Decimal("50.00")
    assert progress.remaining_dollars == Decimal(0)


def test_profit_target_progress_floored_at_zero_for_losing_position() -> None:
    progress = evaluate_profit_target(profit_loss=Decimal("-198.90"), target_dollars=Decimal("300.00"))
    assert progress.reached is False
    assert progress.progress_dollars == Decimal(0)
    assert progress.remaining_dollars == Decimal("498.90")


def test_realized_pnl_single_sell_profit() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("10", "150.00", date(2026, 1, 10)),
    ]
    assert compute_realized_pnl(trades) == [None, Decimal(500)]


def test_realized_pnl_single_sell_loss() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("10", "80.00", date(2026, 1, 10)),
    ]
    assert compute_realized_pnl(trades) == [None, Decimal(-200)]


def test_realized_pnl_multiple_partial_sells_at_different_avg_costs() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("4", "150.00", date(2026, 1, 10)),
        _buy("10", "200.00", date(2026, 2, 1)),
        _sell("5", "180.00", date(2026, 2, 10)),
    ]
    assert compute_realized_pnl(trades) == [None, Decimal(200), None, Decimal("87.5")]


def test_realized_pnl_position_closed_then_reopened_then_sold() -> None:
    trades = [
        _buy("10", "100.00", date(2026, 1, 1)),
        _sell("10", "150.00", date(2026, 1, 10)),
        _buy("5", "200.00", date(2026, 2, 1)),
        _sell("5", "250.00", date(2026, 2, 10)),
    ]
    assert compute_realized_pnl(trades) == [None, Decimal(500), None, Decimal(250)]


def test_realized_pnl_oversell_raises_position_error() -> None:
    trades = [
        _buy("5", "100.00", date(2026, 1, 1)),
        _sell("10", "150.00", date(2026, 1, 10)),
    ]
    with pytest.raises(PositionError):
        compute_realized_pnl(trades)
