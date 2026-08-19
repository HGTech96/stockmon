from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from stockmon.core.indicators import Indicators
from stockmon.core.position import PositionValue

RSI_LOW = Decimal(40)
RSI_HIGH = Decimal(70)
NEAR_LOW_PCT = Decimal(5)
NEAR_HIGH_PCT = Decimal(5)
SHARP_1D_PCT = Decimal(5)
SHARP_7D_PCT = Decimal(10)
ENTRY_BUY_MIN_PASSING = 3

SHARP_MOVE_TEXT = "Sharp recent price move — check the news before acting."

Label = Literal["BUY", "WAIT", "SELL"]
SuggestionType = Literal["entry", "exit"]


@dataclass(frozen=True)
class ChecklistItem:
    id: str
    text: str
    passed: bool


@dataclass(frozen=True)
class Suggestion:
    label: Label
    type: SuggestionType
    checklist: list[ChecklistItem]
    note: str | None


@dataclass(frozen=True)
class Warning:
    reason: Literal["1d_move", "7d_move"]
    text: str


def evaluate_entry(indicators: Indicators) -> Suggestion:
    checklist = [
        ChecklistItem(
            id="price_below_30d_avg",
            text="Price is below its 30-day average",
            passed=indicators.current_price < indicators.thirty_day_average,
        ),
        ChecklistItem(
            id="near_30d_low",
            text="Price is close to its 30-day low",
            passed=indicators.distance_from_low_pct <= NEAR_LOW_PCT,
        ),
        ChecklistItem(
            id="rsi_low",
            text=f"RSI is relatively low ({indicators.rsi:.0f})",
            passed=indicators.rsi < RSI_LOW,
        ),
        ChecklistItem(
            id="volume_above_avg",
            text="Trading volume is above average",
            passed=indicators.todays_volume > indicators.average_volume,
        ),
    ]
    passing = sum(1 for item in checklist if item.passed)
    label: Label = "BUY" if passing >= ENTRY_BUY_MIN_PASSING else "WAIT"
    return Suggestion(label=label, type="entry", checklist=checklist, note=None)


def evaluate_exit(
    indicators: Indicators, position_value: PositionValue, target_dollars: Decimal
) -> Suggestion:
    profit_target_reached = position_value.profit_loss >= target_dollars
    rsi_high = indicators.rsi > RSI_HIGH
    near_30d_high = indicators.distance_from_high_pct >= -NEAR_HIGH_PCT

    checklist = [
        ChecklistItem(
            id="profit_target_reached",
            text="Profit target has been reached",
            passed=profit_target_reached,
        ),
        ChecklistItem(
            id="rsi_high",
            text=f"RSI is relatively high ({indicators.rsi:.0f})",
            passed=rsi_high,
        ),
        ChecklistItem(
            id="near_30d_high",
            text="Price is close to its 30-day high",
            passed=near_30d_high,
        ),
    ]

    note = None
    if profit_target_reached and (rsi_high or near_30d_high):
        label: Label = "SELL"
    else:
        label = "WAIT"
        if profit_target_reached:
            note = "Profit target reached — consider your plan."

    return Suggestion(label=label, type="exit", checklist=checklist, note=note)


def evaluate_stock(
    indicators: Indicators,
    position_value: PositionValue | None,
    target_dollars: Decimal,
) -> Suggestion:
    """position_value is None for stocks not owned -> entry evaluation only.
    Otherwise runs both and applies precedence: exit SELL > entry BUY > WAIT
    (exit checklist)."""
    entry = evaluate_entry(indicators)
    if position_value is None:
        return entry

    exit_ = evaluate_exit(indicators, position_value, target_dollars)
    if exit_.label == "SELL":
        return exit_
    if entry.label == "BUY":
        return entry
    return exit_


def detect_sharp_move(indicators: Indicators) -> Warning | None:
    if abs(indicators.change_1d_pct) > SHARP_1D_PCT:
        return Warning(reason="1d_move", text=SHARP_MOVE_TEXT)
    if abs(indicators.change_7d_pct) > SHARP_7D_PCT:
        return Warning(reason="7d_move", text=SHARP_MOVE_TEXT)
    return None
