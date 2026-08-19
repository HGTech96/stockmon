from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.position import Position, TradeEvent, derive_position
from stockmon.db.models import Stock
from stockmon.db.models import Trade as TradeRow


class TradeValidationError(Exception):
    pass


@dataclass(frozen=True)
class TradeResult:
    trade: TradeRow
    updated_position: Position | None


def _load_trade_events(db: Session, stock_id: int) -> list[TradeEvent]:
    rows = (
        db.query(TradeRow)
        .filter(TradeRow.stock_id == stock_id)
        .order_by(TradeRow.trade_date, TradeRow.id)
        .all()
    )
    return [
        TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
        for row in rows
    ]


def record_trade(
    db: Session,
    ticker: str,
    action: Literal["buy", "sell"],
    shares: Decimal,
    price_per_share: Decimal,
    trade_date: date,
) -> TradeResult:
    """Validates the request, inserts the Trade row, then recomputes the
    position by replaying the FULL trade history (including the new row)
    through derive_position() — the single source of truth for position
    math, never hand-adjusted."""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if stock is None:
        raise TradeValidationError(f"'{ticker}' is not on the watchlist")
    if shares <= 0:
        raise TradeValidationError("Shares must be greater than 0")
    if price_per_share <= 0:
        raise TradeValidationError("Price per share must be greater than 0")
    if trade_date > date.today():
        raise TradeValidationError("Trade date cannot be in the future")

    existing_events = _load_trade_events(db, stock.id)

    if action == "sell":
        position_before = derive_position(existing_events)
        if position_before is None:
            raise TradeValidationError(f"No open position in {ticker} to sell")
        if shares > position_before.shares_held:
            raise TradeValidationError(
                f"Cannot sell {shares} shares of {ticker}; only {position_before.shares_held} held"
            )

    trade = TradeRow(
        stock_id=stock.id,
        action=action,
        shares=shares,
        price_per_share=price_per_share,
        trade_date=trade_date,
    )
    db.add(trade)
    db.flush()

    all_events = existing_events + [
        TradeEvent(action=action, shares=shares, price_per_share=price_per_share, date=trade_date)
    ]
    all_events.sort(key=lambda e: e.date)
    updated_position = derive_position(all_events)

    db.commit()
    db.refresh(trade)

    return TradeResult(trade=trade, updated_position=updated_position)
