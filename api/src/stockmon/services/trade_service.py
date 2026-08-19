from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.position import Position, TradeEvent, compute_realized_pnl, derive_position
from stockmon.db.models import Stock
from stockmon.db.models import Trade as TradeRow


class TradeValidationError(Exception):
    pass


@dataclass(frozen=True)
class TradeResult:
    trade: TradeRow
    updated_position: Position | None


@dataclass(frozen=True)
class TradeHistoryEntry:
    id: int
    ticker: str
    company_name: str
    action: Literal["buy", "sell"]
    shares: Decimal
    price_per_share: Decimal
    total_usd: Decimal
    realized_pnl_usd: Decimal | None
    date: date


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


def list_trade_history(db: Session) -> list[TradeHistoryEntry]:
    """All trades across the watchlist, newest first. Realized P/L is
    computed per-ticker (compute_realized_pnl needs each stock's own
    chronological trade sequence to replay average cost correctly)."""
    stocks = {stock.id: stock for stock in db.query(Stock).all()}
    rows = db.query(TradeRow).order_by(TradeRow.trade_date, TradeRow.id).all()

    rows_by_stock: dict[int, list[TradeRow]] = {}
    for row in rows:
        rows_by_stock.setdefault(row.stock_id, []).append(row)

    realized_pnl_by_row_id: dict[int, Decimal | None] = {}
    for stock_id, stock_rows in rows_by_stock.items():
        events = [
            TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
            for row in stock_rows
        ]
        for row, realized in zip(stock_rows, compute_realized_pnl(events)):
            realized_pnl_by_row_id[row.id] = realized

    entries = [
        TradeHistoryEntry(
            id=row.id,
            ticker=stocks[row.stock_id].ticker,
            company_name=stocks[row.stock_id].company_name,
            action=row.action,
            shares=row.shares,
            price_per_share=row.price_per_share,
            total_usd=row.shares * row.price_per_share,
            realized_pnl_usd=realized_pnl_by_row_id[row.id],
            date=row.trade_date,
        )
        for row in rows
    ]
    entries.sort(key=lambda e: (e.date, e.id), reverse=True)
    return entries
