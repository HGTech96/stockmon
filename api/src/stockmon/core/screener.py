from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from stockmon.core.evaluation import detect_sharp_move, evaluate_entry
from stockmon.core.indicators import (
    InsufficientHistoryError,
    calculate_indicators,
    calculate_price_snapshot,
    price_vs_30d_avg_pct,
)
from stockmon.core.market_data import DailyBar

Status = Literal["ok", "insufficient_history"]


@dataclass(frozen=True)
class ScreenerEvaluation:
    status: Status
    current_price: Decimal | None
    change_1d_pct: Decimal | None
    change_7d_pct: Decimal | None
    suggestion_label: Literal["BUY", "WAIT"] | None
    conditions_met: int | None
    conditions_total: int | None
    rsi: Decimal | None
    price_vs_30d_avg_pct: Decimal | None
    sharp_move: bool | None


def evaluate_screener_bars(bars: list[DailyBar]) -> ScreenerEvaluation:
    """bars sorted oldest-first, from a live/batch fetch (not the DB).
    Entry-only, no position/exit -- screener stocks are never owned.
    Mirrors stock_service.evaluate_stock_snapshot's insufficient-history
    fallback (a price snapshot when there's at least one bar but fewer
    than MIN_HISTORY_DAYS), minus everything position-related."""
    try:
        indicators = calculate_indicators(bars)
    except InsufficientHistoryError:
        snapshot = calculate_price_snapshot(bars)
        return ScreenerEvaluation(
            status="insufficient_history",
            current_price=snapshot.current_price if snapshot else None,
            change_1d_pct=snapshot.change_1d_pct if snapshot else None,
            change_7d_pct=None,
            suggestion_label=None,
            conditions_met=None,
            conditions_total=None,
            rsi=None,
            price_vs_30d_avg_pct=None,
            sharp_move=None,
        )

    suggestion = evaluate_entry(indicators)
    conditions_met = sum(1 for item in suggestion.checklist if item.passed)
    warning = detect_sharp_move(indicators)

    return ScreenerEvaluation(
        status="ok",
        current_price=indicators.current_price,
        change_1d_pct=indicators.change_1d_pct,
        change_7d_pct=indicators.change_7d_pct,
        suggestion_label=suggestion.label,  # type: ignore[arg-type]
        conditions_met=conditions_met,
        conditions_total=len(suggestion.checklist),
        rsi=indicators.rsi,
        price_vs_30d_avg_pct=price_vs_30d_avg_pct(indicators),
        sharp_move=warning is not None,
    )
