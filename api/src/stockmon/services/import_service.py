"""Bulk CSV history importer. Orchestration only -- parses a chronologically
ordered CSV of past deposits/withdrawals/buys/sells and replays every row
through the same sequence-validators the live write paths use
(derive_position, validate_cash_sequence), on top of the current DB state.
Nothing is written until every row has survived validation. Per-user: every
row is imported against one user's watchlist and cash ledger.
"""

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.cash import CashError, CashFlowEvent
from stockmon.core.position import PositionError, TradeEvent, derive_position
from stockmon.db.models import CashEvent as CashEventRow
from stockmon.db.models import Trade as TradeRow
from stockmon.db.models import WatchlistEntry
from stockmon.services.cash_service import (
    load_all_cash_event_flow_events,
    load_all_trade_flow_events,
    validate_cash_sequence,
)

_KINDS = {"deposit", "withdraw", "buy", "sell"}
_TRADE_KINDS = {"buy", "sell"}
_CASH_KINDS = {"deposit", "withdraw"}
_REQUIRED_COLUMNS = ["date", "type", "ticker", "shares", "price", "amount"]


@dataclass(frozen=True)
class ImportRow:
    line: int  # 1-based CSV line number (header = line 1)
    event_date: date
    kind: Literal["deposit", "withdraw", "buy", "sell"]
    ticker: str | None
    shares: Decimal | None
    price_per_share: Decimal | None
    amount: Decimal | None


class ImportError(Exception):
    """Message always names the offending line number and reason."""


@dataclass(frozen=True)
class ImportSummary:
    trades_added: int
    cash_events_added: int


def _parse_decimal(value: str, line: int, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ImportError(f"line {line}: invalid {field} '{value}'") from exc
    return parsed


def _parse_positive_decimal(value: str, line: int, field: str) -> Decimal:
    parsed = _parse_decimal(value, line, field)
    if parsed <= 0:
        raise ImportError(f"line {line}: {field} must be greater than 0")
    return parsed


def _parse_date(value: str, line: int) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ImportError(f"line {line}: invalid date '{value}' (expected YYYY-MM-DD)") from exc
    if parsed > date.today():
        raise ImportError(f"line {line}: date cannot be in the future")
    return parsed


def parse_csv_rows(fileobj) -> list[ImportRow]:
    """Reads the header + all data rows. Validates per-row shape: `type` is
    one of the four kinds; the fields required for that kind are present and
    parseable (and positive); dates are ISO YYYY-MM-DD, not in the future.
    Fields irrelevant to a row's kind are ignored, even if populated. Raises
    ImportError naming the line on any parse problem. No DB access here --
    ticker-exists checking needs a session and happens in import_rows."""
    reader = csv.DictReader(fileobj)
    if reader.fieldnames is None or list(reader.fieldnames) != _REQUIRED_COLUMNS:
        got = ",".join(reader.fieldnames or [])
        raise ImportError(f"line 1: header must be exactly '{','.join(_REQUIRED_COLUMNS)}', got '{got}'")

    rows: list[ImportRow] = []
    for line, raw in enumerate(reader, start=2):
        kind = (raw.get("type") or "").strip()
        if kind not in _KINDS:
            raise ImportError(f"line {line}: unknown type '{kind}'")

        event_date = _parse_date((raw.get("date") or "").strip(), line)

        if kind in _TRADE_KINDS:
            ticker = (raw.get("ticker") or "").strip()
            if not ticker:
                raise ImportError(f"line {line}: {kind} requires a ticker")
            shares_raw = (raw.get("shares") or "").strip()
            price_raw = (raw.get("price") or "").strip()
            if not shares_raw:
                raise ImportError(f"line {line}: {kind} requires shares")
            if not price_raw:
                raise ImportError(f"line {line}: {kind} requires price")
            shares = _parse_positive_decimal(shares_raw, line, "shares")
            price_per_share = _parse_positive_decimal(price_raw, line, "price")
            amount = None
        else:
            amount_raw = (raw.get("amount") or "").strip()
            if not amount_raw:
                raise ImportError(f"line {line}: {kind} requires amount")
            amount = _parse_positive_decimal(amount_raw, line, "amount")
            ticker = None
            shares = None
            price_per_share = None

        rows.append(
            ImportRow(
                line=line,
                event_date=event_date,
                kind=kind,
                ticker=ticker,
                shares=shares,
                price_per_share=price_per_share,
                amount=amount,
            )
        )
    return rows


def _dup_key(
    event_date: date,
    kind: str,
    ticker: str | None,
    shares: Decimal | None,
    price_per_share: Decimal | None,
    amount: Decimal | None,
) -> tuple:
    return (event_date, kind, ticker, shares, price_per_share, amount)


def _existing_dup_keys(db: Session, user_id: int, tickers_by_entry_id: dict[int, str]) -> set[tuple]:
    keys = set()
    for row in (
        db.query(TradeRow)
        .join(WatchlistEntry, TradeRow.watchlist_entry_id == WatchlistEntry.id)
        .filter(WatchlistEntry.user_id == user_id)
        .all()
    ):
        keys.add(
            _dup_key(
                row.trade_date, row.action, tickers_by_entry_id[row.watchlist_entry_id], row.shares, row.price_per_share, None
            )
        )
    for row in db.query(CashEventRow).filter(CashEventRow.user_id == user_id).all():
        keys.add(_dup_key(row.event_date, row.type, None, None, None, row.amount_usd))
    return keys


def import_rows(db: Session, user_id: int, rows: list[ImportRow]) -> ImportSummary:
    """Pass 1 (no writes): replays every row, in file order, against the
    current DB state via derive_position (per ticker) and
    validate_cash_sequence (global), plus duplicate checks against both the
    pre-import DB snapshot and earlier rows already parsed from this CSV --
    all scoped to `user_id`'s own watchlist and cash ledger. Raises
    ImportError naming the line on the first failure. Pass 2 (only on full
    success): inserts every Trade/CashEvent row and commits once."""
    entries = db.query(WatchlistEntry).filter(WatchlistEntry.user_id == user_id).all()
    entries_by_ticker = {entry.ticker.ticker: entry for entry in entries}
    tickers_by_entry_id = {entry.id: ticker for ticker, entry in entries_by_ticker.items()}

    existing_dup_keys = _existing_dup_keys(db, user_id, tickers_by_entry_id)
    seen_in_csv: set[tuple] = set()

    trade_events_by_ticker: dict[str, list[TradeEvent]] = {ticker: [] for ticker in entries_by_ticker}
    for row in (
        db.query(TradeRow)
        .join(WatchlistEntry, TradeRow.watchlist_entry_id == WatchlistEntry.id)
        .filter(WatchlistEntry.user_id == user_id)
        .order_by(TradeRow.trade_date, TradeRow.id)
        .all()
    ):
        ticker = tickers_by_entry_id[row.watchlist_entry_id]
        trade_events_by_ticker[ticker].append(
            TradeEvent(action=row.action, shares=row.shares, price_per_share=row.price_per_share, date=row.trade_date)
        )

    global_cash_flows = load_all_trade_flow_events(db, user_id) + load_all_cash_event_flow_events(db, user_id)

    for row in rows:
        key = _dup_key(row.event_date, row.kind, row.ticker, row.shares, row.price_per_share, row.amount)
        if key in existing_dup_keys:
            raise ImportError(f"line {row.line}: duplicate of an existing record")
        if key in seen_in_csv:
            raise ImportError(f"line {row.line}: duplicate of an earlier row in this CSV")
        seen_in_csv.add(key)

        if row.kind in _TRADE_KINDS:
            if row.ticker not in entries_by_ticker:
                raise ImportError(f"line {row.line}: '{row.ticker}' is not on the watchlist")

            candidate_events = sorted(
                trade_events_by_ticker[row.ticker]
                + [TradeEvent(action=row.kind, shares=row.shares, price_per_share=row.price_per_share, date=row.event_date)],
                key=lambda e: e.date,
            )
            try:
                derive_position(candidate_events)
            except PositionError as exc:
                raise ImportError(f"line {row.line}: {exc}") from exc
            trade_events_by_ticker[row.ticker] = candidate_events

            cash_flow = CashFlowEvent(kind=row.kind, amount=row.shares * row.price_per_share, date=row.event_date)
        else:
            cash_flow = CashFlowEvent(kind=row.kind, amount=row.amount, date=row.event_date)

        candidate_cash_flows = global_cash_flows + [cash_flow]
        try:
            validate_cash_sequence(candidate_cash_flows)
        except CashError as exc:
            raise ImportError(f"line {row.line}: {exc}") from exc
        global_cash_flows = candidate_cash_flows

    trades_added = 0
    cash_events_added = 0
    for row in rows:
        if row.kind in _TRADE_KINDS:
            db.add(
                TradeRow(
                    watchlist_entry_id=entries_by_ticker[row.ticker].id,
                    action=row.kind,
                    shares=row.shares,
                    price_per_share=row.price_per_share,
                    trade_date=row.event_date,
                )
            )
            trades_added += 1
        else:
            db.add(CashEventRow(user_id=user_id, type=row.kind, amount_usd=row.amount, event_date=row.event_date))
            cash_events_added += 1
    db.commit()

    return ImportSummary(trades_added=trades_added, cash_events_added=cash_events_added)
