from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.evaluation import Suggestion, Warning, detect_sharp_move, evaluate_stock
from stockmon.core.indicators import (
    Indicators,
    InsufficientHistoryError,
    calculate_indicators,
    calculate_price_snapshot,
)
from stockmon.core.market_data import DailyBar
from stockmon.core.position import Position, PositionValue, TradeEvent, derive_position, value_position
from stockmon.db.models import DailyPrice, Stock, Trade

Status = Literal["ok", "insufficient_history"]


class StockNotFoundError(Exception):
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__(f"'{ticker}' is not on the watchlist")


@dataclass(frozen=True)
class StockEvaluation:
    stock: Stock
    bars: list[DailyBar]
    status: Status
    current_price: Decimal | None
    change_1d_pct: Decimal | None
    indicators: Indicators | None
    days_available: int
    position: Position | None
    position_value: PositionValue | None
    suggestion: Suggestion | None
    warning: Warning | None


def _load_bars(db: Session, stock_id: int) -> list[DailyBar]:
    rows = (
        db.query(DailyPrice)
        .filter(DailyPrice.stock_id == stock_id)
        .order_by(DailyPrice.trade_date)
        .all()
    )
    return [
        DailyBar(
            date=row.trade_date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
        )
        for row in rows
    ]


def _load_trade_events(db: Session, stock_id: int) -> list[TradeEvent]:
    rows = (
        db.query(Trade)
        .filter(Trade.stock_id == stock_id)
        .order_by(Trade.trade_date, Trade.id)
        .all()
    )
    return [
        TradeEvent(
            action=row.action,  # type: ignore[arg-type]
            shares=row.shares,
            price_per_share=row.price_per_share,
            date=row.trade_date,
        )
        for row in rows
    ]


def evaluate_stock_snapshot(db: Session, stock: Stock, target_dollars: Decimal) -> StockEvaluation:
    """Loads price history and trade history for a stock and runs every
    core/ evaluation against it. Falls back to a bare price snapshot when
    there isn't enough history for full indicators, since the dashboard and
    portfolio still need to show currentPrice/position value for those
    stocks. Position value only needs the latest close, so it's computed
    even when status is insufficient_history."""
    bars = _load_bars(db, stock.id)

    indicators: Indicators | None = None
    current_price: Decimal | None = None
    change_1d_pct: Decimal | None = None
    status: Status = "insufficient_history"

    try:
        indicators = calculate_indicators(bars)
        current_price = indicators.current_price
        change_1d_pct = indicators.change_1d_pct
        status = "ok"
    except InsufficientHistoryError:
        snapshot = calculate_price_snapshot(bars)
        if snapshot is not None:
            current_price = snapshot.current_price
            change_1d_pct = snapshot.change_1d_pct

    position = derive_position(_load_trade_events(db, stock.id))
    position_value: PositionValue | None = None
    if position is not None and current_price is not None:
        position_value = value_position(position, current_price)

    suggestion: Suggestion | None = None
    warning: Warning | None = None
    if indicators is not None:
        suggestion = evaluate_stock(indicators, position_value, target_dollars)
        warning = detect_sharp_move(indicators)

    return StockEvaluation(
        stock=stock,
        bars=bars,
        status=status,
        current_price=current_price,
        change_1d_pct=change_1d_pct,
        indicators=indicators,
        days_available=len(bars),
        position=position,
        position_value=position_value,
        suggestion=suggestion,
        warning=warning,
    )
