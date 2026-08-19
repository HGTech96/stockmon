from decimal import Decimal

from stockmon.core.evaluation import (
    detect_sharp_move,
    evaluate_entry,
    evaluate_exit,
    evaluate_stock,
)
from stockmon.core.indicators import Indicators
from stockmon.core.position import PositionValue


def _indicators(**overrides: object) -> Indicators:
    base: dict[str, object] = dict(
        current_price=Decimal(100),
        change_1d_pct=Decimal(0),
        change_7d_pct=Decimal(0),
        thirty_day_average=Decimal(100),
        thirty_day_high=Decimal(100),
        thirty_day_low=Decimal(100),
        distance_from_high_pct=Decimal(0),
        distance_from_low_pct=Decimal(0),
        rsi=Decimal(50),
        todays_volume=1000,
        average_volume=Decimal(1000),
        volume_vs_average_pct=Decimal(100),
    )
    base.update(overrides)
    return Indicators(**base)  # type: ignore[arg-type]


def _position_value(profit_loss: Decimal) -> PositionValue:
    return PositionValue(
        current_value=Decimal(1000) + profit_loss,
        profit_loss=profit_loss,
        profit_loss_pct=Decimal(0),
    )


# --- entry ---


def test_entry_all_four_pass_is_buy() -> None:
    indicators = _indicators(
        current_price=Decimal(90),
        thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal("2.27"),
        rsi=Decimal(30),
        todays_volume=2000,
        average_volume=Decimal(1000),
    )
    suggestion = evaluate_entry(indicators)
    assert suggestion.label == "BUY"
    assert suggestion.type == "entry"
    assert all(item.passed for item in suggestion.checklist)


def test_entry_exactly_three_of_four_is_buy() -> None:
    indicators = _indicators(
        current_price=Decimal(90),
        thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(2),
        rsi=Decimal(30),
        todays_volume=500,
        average_volume=Decimal(1000),
    )
    suggestion = evaluate_entry(indicators)
    assert suggestion.label == "BUY"


def test_entry_two_of_four_is_wait() -> None:
    indicators = _indicators(
        current_price=Decimal(90),
        thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(2),
        rsi=Decimal(50),
        todays_volume=500,
        average_volume=Decimal(1000),
    )
    suggestion = evaluate_entry(indicators)
    assert suggestion.label == "WAIT"


def test_entry_zero_of_four_is_wait() -> None:
    indicators = _indicators(
        current_price=Decimal(110),
        thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(20),
        rsi=Decimal(80),
        todays_volume=500,
        average_volume=Decimal(1000),
    )
    suggestion = evaluate_entry(indicators)
    assert suggestion.label == "WAIT"
    assert not any(item.passed for item in suggestion.checklist)


# --- exit ---


def test_exit_target_and_rsi_high_is_sell() -> None:
    indicators = _indicators(rsi=Decimal(75), distance_from_high_pct=Decimal(-20))
    suggestion = evaluate_exit(indicators, _position_value(Decimal(60)), target_dollars=Decimal(50))
    assert suggestion.label == "SELL"
    assert suggestion.note is None


def test_exit_target_and_near_high_is_sell() -> None:
    indicators = _indicators(rsi=Decimal(50), distance_from_high_pct=Decimal(-3))
    suggestion = evaluate_exit(indicators, _position_value(Decimal(60)), target_dollars=Decimal(50))
    assert suggestion.label == "SELL"


def test_exit_target_alone_is_wait_with_note() -> None:
    indicators = _indicators(rsi=Decimal(50), distance_from_high_pct=Decimal(-20))
    suggestion = evaluate_exit(indicators, _position_value(Decimal(60)), target_dollars=Decimal(50))
    assert suggestion.label == "WAIT"
    assert suggestion.note == "Profit target reached — consider your plan."


def test_exit_technical_alone_without_target_is_wait_no_note() -> None:
    indicators = _indicators(rsi=Decimal(80), distance_from_high_pct=Decimal(-20))
    suggestion = evaluate_exit(indicators, _position_value(Decimal(10)), target_dollars=Decimal(50))
    assert suggestion.label == "WAIT"
    assert suggestion.note is None


def test_exit_never_sells_at_a_loss() -> None:
    indicators = _indicators(rsi=Decimal(80), distance_from_high_pct=Decimal(-1))
    suggestion = evaluate_exit(indicators, _position_value(Decimal(-50)), target_dollars=Decimal(50))
    assert suggestion.label == "WAIT"
    assert suggestion.note is None


# --- precedence (evaluate_stock) ---


def test_evaluate_stock_not_owned_runs_entry_only() -> None:
    indicators = _indicators(
        current_price=Decimal(90), thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(2), rsi=Decimal(30),
        todays_volume=2000, average_volume=Decimal(1000),
    )
    suggestion = evaluate_stock(indicators, position_value=None, target_dollars=Decimal(50))
    assert suggestion.type == "entry"
    assert suggestion.label == "BUY"


def test_evaluate_stock_owned_sell_beats_buy() -> None:
    indicators = _indicators(
        current_price=Decimal(90), thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(2), rsi=Decimal(75),
        todays_volume=2000, average_volume=Decimal(1000),
        distance_from_high_pct=Decimal(-1),
    )
    suggestion = evaluate_stock(indicators, _position_value(Decimal(60)), target_dollars=Decimal(50))
    assert suggestion.type == "exit"
    assert suggestion.label == "SELL"


def test_evaluate_stock_owned_buy_wins_over_exit_wait() -> None:
    indicators = _indicators(
        current_price=Decimal(90), thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(2), rsi=Decimal(30),
        todays_volume=2000, average_volume=Decimal(1000),
        distance_from_high_pct=Decimal(-20),
    )
    # target reached but no technical -> exit alone would be WAIT + note
    suggestion = evaluate_stock(indicators, _position_value(Decimal(60)), target_dollars=Decimal(50))
    assert suggestion.type == "entry"
    assert suggestion.label == "BUY"
    assert suggestion.note is None


def test_evaluate_stock_owned_both_wait_returns_exit_checklist_with_note() -> None:
    indicators = _indicators(
        current_price=Decimal(110), thirty_day_average=Decimal(100),
        distance_from_low_pct=Decimal(20), rsi=Decimal(50),
        todays_volume=500, average_volume=Decimal(1000),
        distance_from_high_pct=Decimal(-20),
    )
    suggestion = evaluate_stock(indicators, _position_value(Decimal(60)), target_dollars=Decimal(50))
    assert suggestion.type == "exit"
    assert suggestion.label == "WAIT"
    assert suggestion.note == "Profit target reached — consider your plan."


# --- sharp-move warning ---


def test_sharp_move_1d_triggers() -> None:
    indicators = _indicators(change_1d_pct=Decimal("5.01"), change_7d_pct=Decimal(0))
    warning = detect_sharp_move(indicators)
    assert warning is not None
    assert warning.reason == "1d_move"


def test_sharp_move_1d_boundary_does_not_trigger() -> None:
    indicators = _indicators(change_1d_pct=Decimal(5), change_7d_pct=Decimal(0))
    assert detect_sharp_move(indicators) is None


def test_sharp_move_7d_triggers() -> None:
    indicators = _indicators(change_1d_pct=Decimal(1), change_7d_pct=Decimal("10.01"))
    warning = detect_sharp_move(indicators)
    assert warning is not None
    assert warning.reason == "7d_move"


def test_sharp_move_7d_boundary_does_not_trigger() -> None:
    indicators = _indicators(change_1d_pct=Decimal(1), change_7d_pct=Decimal(10))
    assert detect_sharp_move(indicators) is None


def test_sharp_move_both_trigger_1d_wins() -> None:
    indicators = _indicators(change_1d_pct=Decimal(6), change_7d_pct=Decimal(15))
    warning = detect_sharp_move(indicators)
    assert warning is not None
    assert warning.reason == "1d_move"


def test_sharp_move_neither_triggers() -> None:
    indicators = _indicators(change_1d_pct=Decimal(1), change_7d_pct=Decimal(1))
    assert detect_sharp_move(indicators) is None


def test_sharp_move_negative_move_also_triggers() -> None:
    indicators = _indicators(change_1d_pct=Decimal(-6), change_7d_pct=Decimal(0))
    warning = detect_sharp_move(indicators)
    assert warning is not None
    assert warning.reason == "1d_move"
