from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

_INCREASES = {"deposit", "sell"}


class CashError(Exception):
    """Raised when a withdrawal or buy would drive the cash balance negative
    at some point in the replay."""


@dataclass(frozen=True)
class CashFlowEvent:
    kind: Literal["deposit", "withdraw", "buy", "sell"]
    amount: Decimal
    date: date


def chronological_key(event: CashFlowEvent) -> tuple[date, int]:
    """Sort key: date, then money-in (deposit/sell) before money-out
    (withdraw/buy) on the same date. DELIBERATE business rule, not sort
    stability -- a same-day deposit-then-buy or sell-then-withdraw must
    never be rejected. Do not "simplify" this to id/insertion order."""
    return (event.date, 0 if event.kind in _INCREASES else 1)


def derive_cash_balance(events: list[CashFlowEvent], *, strict: bool = True) -> Decimal:
    """Replays events IN THE GIVEN ORDER (caller sorts via chronological_key).
    +amount for deposit/sell, -amount for withdraw/buy. With strict=True (the
    write path — validating a candidate buy/withdraw/edit/delete before it's
    committed), raises CashError the instant balance would go negative.
    strict=False (the read path — just reporting the current balance for
    display) never raises, so a GET can never 500 on account of the
    invariant; it should hold by construction since every write is validated
    strict, but a display path must not depend on that holding forever.
    Returns the final balance."""
    balance = Decimal(0)
    for event in events:
        if event.kind in _INCREASES:
            balance += event.amount
        else:
            balance -= event.amount
            if strict and balance < 0:
                raise CashError(f"insufficient cash on {event.date}: balance would be {balance}")
    return balance
