from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.position import Position, PositionError, TradeEvent, compute_realized_pnl, derive_position
from stockmon.db.models import Stock
from stockmon.db.models import Trade as TradeRow


class TradeValidationError(Exception):
    pass


class TradeNotFoundError(Exception):
    def __init__(self, trade_id: int) -> None:
        self.trade_id = trade_id
        super().__init__(f"Trade {trade_id} not found")


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


def _validate_trade_fields(shares: Decimal, price_per_share: Decimal, trade_date: date) -> None:
    """Shared by record_trade and update_trade -- the one place these three
    invariants are enforced."""
    if shares <= 0:
        raise TradeValidationError("Shares must be greater than 0")
    if price_per_share <= 0:
        raise TradeValidationError("Price per share must be greater than 0")
    if trade_date > date.today():
        raise TradeValidationError("Trade date cannot be in the future")


def _load_trade_rows(db: Session, stock_id: int) -> list[TradeRow]:
    return (
        db.query(TradeRow)
        .filter(TradeRow.stock_id == stock_id)
        .order_by(TradeRow.trade_date, TradeRow.id)
        .all()
    )


def _to_events(rows: list[TradeRow]) -> list[TradeEvent]:
    return [
        TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
        for row in rows
    ]


def _load_trade_events(db: Session, stock_id: int) -> list[TradeEvent]:
    return _to_events(_load_trade_rows(db, stock_id))


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
    _validate_trade_fields(shares, price_per_share, trade_date)

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


def update_trade(
    db: Session,
    trade_id: int,
    shares: Decimal,
    price_per_share: Decimal,
    trade_date: date,
) -> TradeResult:
    """Ticker and action are immutable. Builds the full post-edit event list
    for the trade's ticker (rows are already loaded in (date, id) order, so
    swapping the edited entry's fields in place before a stable date-sort
    relocates only that entry), validates it via derive_position -- the
    single source of truth for the oversell rule -- and only mutates the
    row once validation passes. Never a partial apply."""
    trade = db.query(TradeRow).filter(TradeRow.id == trade_id).first()
    if trade is None:
        raise TradeNotFoundError(trade_id)
    _validate_trade_fields(shares, price_per_share, trade_date)

    rows = _load_trade_rows(db, trade.stock_id)
    candidate_events = [
        TradeEvent(action=row.action, shares=shares, price_per_share=price_per_share, date=trade_date)
        if row.id == trade_id
        else TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
        for row in rows
    ]
    candidate_events.sort(key=lambda e: e.date)

    try:
        updated_position = derive_position(candidate_events)
    except PositionError as exc:
        raise TradeValidationError(str(exc)) from exc

    trade.shares = shares
    trade.price_per_share = price_per_share
    trade.trade_date = trade_date
    db.commit()
    db.refresh(trade)

    return TradeResult(trade=trade, updated_position=updated_position)


def delete_trade(db: Session, trade_id: int) -> Position | None:
    """Builds the event list for the trade's ticker with this trade removed,
    validates via derive_position, then deletes. Returns the recalculated
    position (None if the ticker ends up fully closed / never opened)."""
    trade = db.query(TradeRow).filter(TradeRow.id == trade_id).first()
    if trade is None:
        raise TradeNotFoundError(trade_id)

    remaining_rows = [row for row in _load_trade_rows(db, trade.stock_id) if row.id != trade_id]
    remaining_events = _to_events(remaining_rows)

    try:
        updated_position = derive_position(remaining_events)
    except PositionError as exc:
        raise TradeValidationError(str(exc)) from exc

    db.delete(trade)
    db.commit()

    return updated_position


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
