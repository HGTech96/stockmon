from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.cash import CashError, CashFlowEvent, chronological_key, derive_cash_balance
from stockmon.db.models import CashEvent as CashEventRow
from stockmon.db.models import Trade as TradeRow


class CashValidationError(Exception):
    pass


class CashNotFoundError(Exception):
    def __init__(self, event_id: int) -> None:
        self.event_id = event_id
        super().__init__(f"Cash event {event_id} not found")


@dataclass(frozen=True)
class CashEventEntry:
    id: int
    type: Literal["deposit", "withdraw"]
    amount_usd: Decimal
    date: date


def _validate_cash_fields(amount: Decimal, event_date: date) -> None:
    if amount <= 0:
        raise CashValidationError("Amount must be greater than 0")
    if event_date > date.today():
        raise CashValidationError("Date cannot be in the future")


def trade_row_to_flow_event(row: TradeRow) -> CashFlowEvent:
    return CashFlowEvent(kind=row.action, amount=row.shares * row.price_per_share, date=row.trade_date)


def cash_row_to_flow_event(row: CashEventRow) -> CashFlowEvent:
    return CashFlowEvent(kind=row.type, amount=row.amount_usd, date=row.event_date)


def _load_cash_event_rows(db: Session) -> list[CashEventRow]:
    return db.query(CashEventRow).order_by(CashEventRow.event_date, CashEventRow.id).all()


def load_all_trade_flow_events(db: Session) -> list[CashFlowEvent]:
    """Every trade, every ticker -- the cash side of buys/sells."""
    rows = db.query(TradeRow).order_by(TradeRow.trade_date, TradeRow.id).all()
    return [trade_row_to_flow_event(row) for row in rows]


def load_all_cash_event_flow_events(db: Session) -> list[CashFlowEvent]:
    return [cash_row_to_flow_event(row) for row in _load_cash_event_rows(db)]


def validate_cash_sequence(events: list[CashFlowEvent]) -> Decimal:
    """Sorts via chronological_key and replays via derive_cash_balance (strict
    -- raises the instant balance would go negative) -- the one source of
    truth for the never-negative-cash rule. Lets CashError propagate
    uncaught: each call site raises its OWN contextual message, this
    function only runs the check. WRITE PATH ONLY -- see compute_cash_balance
    for reads."""
    return derive_cash_balance(sorted(events, key=chronological_key))


def compute_cash_balance(events: list[CashFlowEvent]) -> Decimal:
    """Sorts via chronological_key and replays non-strict -- never raises, so
    a GET can never 500. The invariant holds by construction (every write
    goes through validate_cash_sequence first), but a display path must not
    depend on that holding forever."""
    return derive_cash_balance(sorted(events, key=chronological_key), strict=False)


def list_cash_events(db: Session) -> tuple[list[CashEventEntry], Decimal]:
    """events newest-first, plus current cashAvailable."""
    rows = _load_cash_event_rows(db)
    cash_available = compute_cash_balance(
        [cash_row_to_flow_event(row) for row in rows] + load_all_trade_flow_events(db)
    )
    entries = [
        CashEventEntry(id=row.id, type=row.type, amount_usd=row.amount_usd, date=row.event_date)
        for row in rows
    ]
    entries.sort(key=lambda e: (e.date, e.id), reverse=True)
    return entries, cash_available


def record_cash_event(
    db: Session, type_: Literal["deposit", "withdraw"], amount: Decimal, event_date: date
) -> tuple[CashEventRow, Decimal]:
    """Validates fields, builds the candidate full event list (existing
    trades + existing cash events + this new one), validates via
    validate_cash_sequence BEFORE inserting -- atomic, never partial."""
    _validate_cash_fields(amount, event_date)

    candidate = (
        load_all_trade_flow_events(db)
        + load_all_cash_event_flow_events(db)
        + [CashFlowEvent(kind=type_, amount=amount, date=event_date)]
    )
    try:
        cash_available = validate_cash_sequence(candidate)
    except CashError as exc:
        # A deposit can only ever ADD cash, so it can never be the cause of a
        # negative point in the replay -- this branch is unreachable in
        # practice, but CashError must never leak past the service layer
        # uncaught (FastAPI has no handler registered for it, only for
        # CashValidationError), so it's still wrapped defensively.
        message = (
            "Can't withdraw more than your available cash."
            if type_ == "withdraw"
            else "Can't record this deposit — it would leave an earlier point in the cash history negative."
        )
        raise CashValidationError(message) from exc

    row = CashEventRow(type=type_, amount_usd=amount, event_date=event_date)
    db.add(row)
    db.commit()
    db.refresh(row)

    return row, cash_available


def delete_cash_event(db: Session, event_id: int) -> Decimal:
    """Builds the candidate list with this event removed, validates, then
    deletes. Raises CashNotFoundError if id doesn't exist."""
    row = db.get(CashEventRow, event_id)
    if row is None:
        raise CashNotFoundError(event_id)

    remaining_rows = [r for r in _load_cash_event_rows(db) if r.id != event_id]
    candidate = load_all_trade_flow_events(db) + [cash_row_to_flow_event(r) for r in remaining_rows]

    try:
        cash_available = validate_cash_sequence(candidate)
    except CashError as exc:
        raise CashValidationError("Can't remove this — a later buy or withdrawal depends on it.") from exc

    db.delete(row)
    db.commit()

    return cash_available
