from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.cash import CashError, CashFlowEvent
from stockmon.core.position import Position, PositionError, TradeEvent, compute_realized_pnl, derive_position
from stockmon.db.models import Ticker
from stockmon.db.models import Trade as TradeRow
from stockmon.db.models import WatchlistEntry
from stockmon.services.cash_service import (
    load_all_cash_event_flow_events,
    load_all_trade_flow_events,
    trade_row_to_flow_event,
    validate_cash_sequence,
)


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


def _find_watchlist_entry(db: Session, user_id: int, ticker: str) -> WatchlistEntry | None:
    return (
        db.query(WatchlistEntry)
        .join(Ticker, WatchlistEntry.ticker_id == Ticker.id)
        .filter(WatchlistEntry.user_id == user_id, Ticker.ticker == ticker)
        .first()
    )


def _load_trade_rows(db: Session, watchlist_entry_id: int) -> list[TradeRow]:
    return (
        db.query(TradeRow)
        .filter(TradeRow.watchlist_entry_id == watchlist_entry_id)
        .order_by(TradeRow.trade_date, TradeRow.id)
        .all()
    )


def _load_all_trade_rows(db: Session, user_id: int) -> list[TradeRow]:
    return (
        db.query(TradeRow)
        .join(WatchlistEntry, TradeRow.watchlist_entry_id == WatchlistEntry.id)
        .filter(WatchlistEntry.user_id == user_id)
        .order_by(TradeRow.trade_date, TradeRow.id)
        .all()
    )


def _get_own_trade_row(db: Session, user_id: int, trade_id: int) -> TradeRow:
    """Loads a trade by id AND checks it belongs to this user -- a trade
    that exists but belongs to someone else is treated identically to one
    that doesn't exist (TradeNotFoundError -> 404), never leaking that the
    id is valid for another account."""
    row = (
        db.query(TradeRow)
        .join(WatchlistEntry, TradeRow.watchlist_entry_id == WatchlistEntry.id)
        .filter(TradeRow.id == trade_id, WatchlistEntry.user_id == user_id)
        .first()
    )
    if row is None:
        raise TradeNotFoundError(trade_id)
    return row


def _validate_global_cash_sequence(
    db: Session,
    user_id: int,
    candidate_trade_flows: list[CashFlowEvent],
    error_message: str,
) -> None:
    """Rebuilds the full cash-flow picture (the given candidate trade-side
    flows, all of this user's tickers, + their unchanged cash-event log) and
    validates it via validate_cash_sequence -- the one source of truth for
    the never-negative-cash rule. Used by update_trade/delete_trade, which
    must re-check this unconditionally: shrinking or removing a SELL's
    proceeds can strand a later buy or withdrawal just as easily as editing
    a buy can."""
    candidate_cash_flows = candidate_trade_flows + load_all_cash_event_flow_events(db, user_id)
    try:
        validate_cash_sequence(candidate_cash_flows)
    except CashError as exc:
        raise TradeValidationError(error_message) from exc


def _to_events(rows: list[TradeRow]) -> list[TradeEvent]:
    return [
        TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
        for row in rows
    ]


def _load_trade_events(db: Session, watchlist_entry_id: int) -> list[TradeEvent]:
    return _to_events(_load_trade_rows(db, watchlist_entry_id))


def record_trade(
    db: Session,
    user_id: int,
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
    entry = _find_watchlist_entry(db, user_id, ticker)
    if entry is None:
        raise TradeValidationError(f"'{ticker}' is not on the watchlist")
    _validate_trade_fields(shares, price_per_share, trade_date)

    existing_events = _load_trade_events(db, entry.id)

    if action == "sell":
        position_before = derive_position(existing_events)
        if position_before is None:
            raise TradeValidationError(f"No open position in {ticker} to sell")
        if shares > position_before.shares_held:
            raise TradeValidationError(
                f"Cannot sell {shares} shares of {ticker}; only {position_before.shares_held} held"
            )

    if action == "buy":
        candidate_cash_flows = (
            load_all_trade_flow_events(db, user_id)
            + load_all_cash_event_flow_events(db, user_id)
            + [CashFlowEvent(kind="buy", amount=shares * price_per_share, date=trade_date)]
        )
        try:
            validate_cash_sequence(candidate_cash_flows)
        except CashError as exc:
            raise TradeValidationError("Insufficient cash — record a deposit first.") from exc

    trade = TradeRow(
        watchlist_entry_id=entry.id,
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
    user_id: int,
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
    trade = _get_own_trade_row(db, user_id, trade_id)
    _validate_trade_fields(shares, price_per_share, trade_date)

    rows = _load_trade_rows(db, trade.watchlist_entry_id)
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

    candidate_trade_flows = [
        CashFlowEvent(kind=row.action, amount=shares * price_per_share, date=trade_date)
        if row.id == trade_id
        else trade_row_to_flow_event(row)
        for row in _load_all_trade_rows(db, user_id)
    ]
    _validate_global_cash_sequence(
        db, user_id, candidate_trade_flows, "Can't make this change — a later buy or withdrawal depends on it."
    )

    trade.shares = shares
    trade.price_per_share = price_per_share
    trade.trade_date = trade_date
    db.commit()
    db.refresh(trade)

    return TradeResult(trade=trade, updated_position=updated_position)


def delete_trade(db: Session, user_id: int, trade_id: int) -> Position | None:
    """Builds the event list for the trade's ticker with this trade removed,
    validates via derive_position, then deletes. Returns the recalculated
    position (None if the ticker ends up fully closed / never opened)."""
    trade = _get_own_trade_row(db, user_id, trade_id)

    remaining_rows = [row for row in _load_trade_rows(db, trade.watchlist_entry_id) if row.id != trade_id]
    remaining_events = _to_events(remaining_rows)

    try:
        updated_position = derive_position(remaining_events)
    except PositionError as exc:
        raise TradeValidationError(str(exc)) from exc

    candidate_trade_flows = [
        trade_row_to_flow_event(row) for row in _load_all_trade_rows(db, user_id) if row.id != trade_id
    ]
    _validate_global_cash_sequence(
        db, user_id, candidate_trade_flows, "Can't remove this — a later buy or withdrawal depends on it."
    )

    db.delete(trade)
    db.commit()

    return updated_position


def list_trade_history(db: Session, user_id: int) -> list[TradeHistoryEntry]:
    """All of this user's trades across their watchlist, newest first.
    Realized P/L is computed per-ticker (compute_realized_pnl needs each
    stock's own chronological trade sequence to replay average cost
    correctly)."""
    entries_by_id = {
        entry.id: entry
        for entry in db.query(WatchlistEntry).filter(WatchlistEntry.user_id == user_id).all()
    }
    rows = _load_all_trade_rows(db, user_id)

    rows_by_entry: dict[int, list[TradeRow]] = {}
    for row in rows:
        rows_by_entry.setdefault(row.watchlist_entry_id, []).append(row)

    realized_pnl_by_row_id: dict[int, Decimal | None] = {}
    for entry_id, entry_rows in rows_by_entry.items():
        events = [
            TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
            for row in entry_rows
        ]
        for row, realized in zip(entry_rows, compute_realized_pnl(events)):
            realized_pnl_by_row_id[row.id] = realized

    entries = [
        TradeHistoryEntry(
            id=row.id,
            ticker=entries_by_id[row.watchlist_entry_id].ticker.ticker,
            company_name=entries_by_id[row.watchlist_entry_id].ticker.company_name,
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
