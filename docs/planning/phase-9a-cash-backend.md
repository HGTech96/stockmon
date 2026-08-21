# Phase 9a — Cash Model (Backend Only)

## Overview

Implements contract v1.5: a `cash_events` log, cash balance derived by
replaying deposits/withdrawals/buys/sells in chronological order (never a
stored mutable number), an extension of the Phase 8 sequence-replay so buys
and withdrawals can't oversell cash, the six money figures, and
GET/POST `/api/cash` + `DELETE /api/cash/{id}`. No UI this phase — money
block wiring into pages is 9d.

**Design decision: two independent replays, not one merged one.** Shares are
per-ticker; cash is global (crosses all tickers). Rather than one function
checking both invariants in a single pass, `derive_position` (existing, per
ticker) keeps owning the share rule, and a new `derive_cash_balance` (per
transaction history, all tickers + cash events) owns the cash rule. Both are
run — atomically, before any DB write — whenever a trade or cash event is
written. This keeps "every business rule in exactly one core function"
intact rather than merging two unrelated rules into one.

**Same-day ordering rule (confirmed):** when a deposit/sell and a
withdrawal/buy land on the same date, money-in is applied before money-out —
matches how trades actually get recorded (deposit-then-buy, sell-then-
withdraw, same day). This is a real business rule, not a sort-stability
detail: `chronological_key` in `core/cash.py` carries an explicit comment
that money-in-before-money-out on ties is deliberate and must not be
"simplified" to id-order, and the rule is spelled out in
`docs/api-contract.md` v1.5 alongside the replay description.

**Error messages are contextual, not a single generic string** — each
rejection path raises its own wording so the message tells the user what to
do next (see the message table below), rather than one generic "insufficient
cash" that leaves them guessing which change caused it.

**Realized P/L reuse:** `realizedEarned`/`realizedLost` are built from the
per-sell `realizedPnlUsd` values `trade_service.list_trade_history` already
computes — no second replay of the same rule.

**Unrealized P/L reuse:** `unrealizedGainOpen`/`unrealizedLossOpen` are built
from the `PositionValue.profit_loss` values `dashboard_service`/
`portfolio_service` already compute per open position in their existing
per-stock loop — passed in, not recomputed.

**`money` is a sibling field, never nested in `summary` (confirmed).**
`summary` is `null` when `hasTrades` is false, but cash can exist with zero
trades (deposit made, nothing bought yet) — nesting would hide exactly the
state this phase introduces. `money` is present whenever **any cash event OR
any trade exists at all**, independent of `hasTrades`; `null` only in the
genuinely empty case (no cash activity, no trades, ever).

## Files to create/change

```
api/
  alembic/versions/
    <hash>_add_cash_events_table.py      (new)
  src/stockmon/
    db/models.py                         (add: CashEvent)
    core/
      cash.py                            (new: CashError, CashFlowEvent,
                                            derive_cash_balance, chronological_key)
      money.py                           (new: MoneySummary, compute_money_summary)
    services/
      cash_service.py                    (new: CashValidationError, CashNotFoundError,
                                            trade_row_to_flow_event, cash_row_to_flow_event,
                                            load_all_trade_flow_events,
                                            load_all_cash_event_flow_events,
                                            validate_cash_sequence, CashEventEntry,
                                            list_cash_events, record_cash_event,
                                            delete_cash_event)
      money_service.py                   (new: build_money_summary)
      trade_service.py                   (change: record_trade validates cash on
                                            buy; update_trade/delete_trade validate
                                            cash unconditionally)
      dashboard_service.py               (change: Dashboard gains `money`)
      portfolio_service.py               (change: Portfolio gains `money`)
    api/
      schemas/
        cash.py                          (new: CashEventRequest, CashEventSchema,
                                            CashListResponse, CashEventResponse)
        common.py                        (add: MoneySchema)
        dashboard.py                     (DashboardResponse gains `money`)
        portfolio.py                     (PortfolioResponse gains `money`)
      routes/
        cash.py                          (new: GET/POST /api/cash, DELETE /api/cash/{id})
    main.py                              (register cash router; add
                                           CashValidationError/CashNotFoundError handlers)
  tests/
    core/test_cash.py                    (new)
    core/test_money.py                   (new)
    services/test_cash_service.py        (new)
    services/test_money_service.py       (new)
    services/test_trade_service.py       (add: buy-exceeds-cash, edit/delete
                                           invalidating a later buy's cash)
    routes/test_cash_route.py            (new)

docs/api-contract.md                     (no change — v1.5 already appended)
```

## Schemas / interfaces

**core/cash.py**

```python
class CashError(Exception):
    """Raised when a withdrawal or buy would drive the cash balance negative
    at some point in the replay."""

@dataclass(frozen=True)
class CashFlowEvent:
    kind: Literal["deposit", "withdraw", "buy", "sell"]
    amount: Decimal  # always positive
    date: date

def chronological_key(event: CashFlowEvent) -> tuple[date, int]:
    """Sort key: date, then money-in (deposit/sell) before money-out
    (withdraw/buy) on the same date. DELIBERATE business rule, not sort
    stability -- a same-day deposit-then-buy or sell-then-withdraw must
    never be rejected. Do not "simplify" this to id/insertion order."""

def derive_cash_balance(events: list[CashFlowEvent]) -> Decimal:
    """Replays events IN THE GIVEN ORDER (caller sorts via chronological_key).
    +amount for deposit/sell, -amount for withdraw/buy. Raises CashError the
    instant balance would go negative. Returns final balance."""
```

**core/money.py**

```python
@dataclass(frozen=True)
class MoneySummary:
    cash_available: Decimal
    net_deposited: Decimal
    realized_earned: Decimal
    realized_lost: Decimal        # positive number
    unrealized_gain_open: Decimal
    unrealized_loss_open: Decimal  # positive number

def compute_money_summary(
    cash_flow_events: list[CashFlowEvent],
    realized_pnls: list[Decimal],       # one per sell, all tickers
    open_position_pnls: list[Decimal],  # one per currently-open position
) -> MoneySummary:
    """cash_available = derive_cash_balance(sorted events) -- reuses the one
    cash-balance function rather than re-summing. net_deposited = sum of
    deposit amounts minus withdraw amounts. realized_earned/lost and
    unrealized_gain/loss_open are simple sign-split sums of the two input
    lists (loss/lost figures returned positive)."""
```

**services/cash_service.py**

```python
class CashValidationError(Exception):
    pass

class CashNotFoundError(Exception):
    def __init__(self, event_id: int) -> None: ...

@dataclass(frozen=True)
class CashEventEntry:
    id: int
    type: Literal["deposit", "withdraw"]
    amount_usd: Decimal
    date: date

def load_all_trade_flow_events(db: Session) -> list[CashFlowEvent]:
    """Every trade, every ticker -- buy/sell -> CashFlowEvent."""

def load_all_cash_event_flow_events(db: Session) -> list[CashFlowEvent]:
    """Every deposit/withdraw row -> CashFlowEvent."""

def validate_cash_sequence(events: list[CashFlowEvent]) -> Decimal:
    """Sorts via chronological_key and replays via derive_cash_balance -- the
    one source of truth for the never-negative rule. Lets CashError
    propagate uncaught: each call site (buy, withdraw, cash-event delete,
    trade edit/delete) catches it and raises its OWN contextual message
    (see the error-message table below) -- this function only runs the
    check, it doesn't decide what the user should be told."""

def list_cash_events(db: Session) -> tuple[list[CashEventEntry], Decimal]:
    """events newest-first, plus current cashAvailable."""

def record_cash_event(
    db: Session, type_: Literal["deposit", "withdraw"], amount: Decimal, event_date: date
) -> tuple[CashEventRow, Decimal]:
    """Validates fields, builds the candidate full event list (existing trades
    + existing cash events + this new one), validates via
    validate_cash_sequence BEFORE inserting -- atomic, never partial. On a
    withdraw that fails, catches CashError and raises
    CashValidationError("Can't withdraw more than your available cash.")."""

def delete_cash_event(db: Session, event_id: int) -> Decimal:
    """Builds the candidate list with this event removed, validates, then
    deletes. 404 via CashNotFoundError if id doesn't exist. On a failed
    validation (a later buy/withdrawal depended on this event), catches
    CashError and raises CashValidationError("Can't remove this — a later
    buy or withdrawal depends on it.")."""
```

**services/money_service.py**

```python
def has_money_activity(db: Session) -> bool:
    """True if any cash_events row OR any trades row exists at all. Drives
    whether `money` renders (independent of `hasTrades`/`summary` — see the
    sibling-field decision above)."""

def build_money_summary(db: Session, open_position_pnls: list[Decimal]) -> MoneySummary:
    """Gathers cash_flow_events (trades + cash log) and realized_pnls (from
    trade_service.list_trade_history, reusing its existing per-sell
    realizedPnlUsd) and calls compute_money_summary. open_position_pnls is
    passed in by the caller (dashboard_service / portfolio_service), which
    already computed PositionValue.profit_loss per open position -- not
    recomputed here. Only call when has_money_activity(db) is True."""
```

**services/trade_service.py changes**

- `record_trade`: for `action == "buy"`, after the existing checks, build
  `load_all_trade_flow_events(db) + load_all_cash_event_flow_events(db) +
  [this buy as a CashFlowEvent]` and call `validate_cash_sequence`; catch
  `CashError` and raise `TradeValidationError("Insufficient cash — record a
  deposit first.")` (contract-fixed wording). Sells are never checked against
  cash (they only add cash, can't drive it negative).
- `update_trade`: **always** rebuilds the full candidate trade-flow list (all
  tickers, with this edit applied) + the unchanged cash-event flows, and
  calls `validate_cash_sequence` — regardless of whether the edited trade is
  a buy or a sell, since shrinking a sell's proceeds can strand a later buy
  or withdrawal. On `CashError`, raises
  `TradeValidationError("Can't make this change — a later buy or withdrawal
  depends on it.")`.
- `delete_trade`: same rebuild-and-validate, unconditionally. On `CashError`,
  raises `TradeValidationError("Can't remove this — a later buy or
  withdrawal depends on it.")`.

**Error-message table** (each 422 path owns its own wording — no generic
fallback):

| Path | Message |
|---|---|
| POST /api/trades buy exceeds cash | `Insufficient cash — record a deposit first.` |
| POST /api/cash withdraw exceeds cash | `Can't withdraw more than your available cash.` |
| DELETE /api/cash/{id} strands a later buy/withdrawal | `Can't remove this — a later buy or withdrawal depends on it.` |
| PUT /api/trades/{id} strands cash sequence | `Can't make this change — a later buy or withdrawal depends on it.` |
| DELETE /api/trades/{id} strands cash sequence | `Can't remove this — a later buy or withdrawal depends on it.` |

**db/models.py**

```python
class CashEvent(Base):
    __tablename__ = "cash_events"
    __table_args__ = (
        CheckConstraint("amount_usd > 0", name="ck_cash_event_amount_positive"),
        CheckConstraint("type IN ('deposit', 'withdraw')", name="ck_cash_event_type_valid"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(8))
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    event_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

**api/schemas/cash.py**

```python
class CashEventRequest(CamelModel):
    type: Literal["deposit", "withdraw"]
    amount_usd: Decimal
    date: date

class CashEventSchema(CamelModel):
    id: int
    type: Literal["deposit", "withdraw"]
    amount_usd: Money
    date: date

class CashListResponse(CamelModel):
    meta: MetaSchema
    cash_available: Money
    events: list[CashEventSchema]

class CashEventResponse(CamelModel):
    event: CashEventSchema
    cash_available: Money
```

**api/schemas/common.py** (add)

```python
class MoneySchema(CamelModel):
    cash_available: Money
    net_deposited: Money
    realized_earned: Money
    realized_lost: Money
    unrealized_gain_open: Money
    unrealized_loss_open: Money

    @classmethod
    def from_core(cls, summary: MoneySummary) -> "MoneySchema": ...
```

`DashboardResponse.money` and `PortfolioResponse.money` are both
`MoneySchema | None` — a **sibling** of `summary`/`stocks`/`positions`, not
nested inside `summary`. `None` only when `has_money_activity(db)` is False
(no cash events, no trades, ever).

**api/routes/cash.py**

```python
@router.get("/api/cash", response_model=CashListResponse)
def read_cash(db: Session = Depends(get_db)) -> CashListResponse: ...

@router.post("/api/cash", response_model=CashEventResponse, status_code=201)
def create_cash_event(body: CashEventRequest, db: Session = Depends(get_db)) -> CashEventResponse: ...

@router.delete("/api/cash/{id}", status_code=204)
def remove_cash_event(id: int, db: Session = Depends(get_db)) -> None: ...
```

## Tasks

Backend — core
- [x] `core/cash.py`: `CashError`, `CashFlowEvent`, `chronological_key`, `derive_cash_balance`
- [x] `core/money.py`: `MoneySummary`, `compute_money_summary`
- [x] `tests/core/test_cash.py`: replay never-negative rule, same-day tie-break
      (deposit+buy same day → ok; buy+deposit reversed input order → still ok
      because sort re-orders; withdraw exceeding balance → `CashError`; buy
      exceeding balance → `CashError`)
- [x] `tests/core/test_money.py`: each of the six figures in isolation, plus
      **the consistency identity** (`cashAvailable + currentValueOfHoldings
      == netDeposited + realizedEarned - realizedLost + unrealizedGainOpen -
      unrealizedLossOpen`) asserted across a scripted multi-event sequence

Backend — db
- [x] `CashEvent` model in `db/models.py`
- [x] Alembic migration `add_cash_events_table` (down_revision = current head)

Backend — services
- [x] `services/cash_service.py`: validation, flow-event loaders,
      `validate_cash_sequence`, `list_cash_events`, `record_cash_event`,
      `delete_cash_event`
- [x] `services/money_service.py`: `has_money_activity`, `build_money_summary`
- [x] `trade_service.record_trade`: cash check on buy, contextual message
- [x] `trade_service.update_trade` / `delete_trade`: unconditional global cash
      re-validation alongside the existing per-ticker share re-validation,
      each with its own contextual message (see table above)
- [x] `dashboard_service.build_dashboard` / `portfolio_service.get_portfolio`:
      collect `open_position_pnls` from the existing per-stock loop; attach
      `money = build_money_summary(...) if has_money_activity(db) else None`
      as a sibling field to `Dashboard`/`Portfolio` (not nested in summary)
- [x] `tests/services/test_cash_service.py`: deposit, withdraw, withdraw
      exceeding cash (reject), delete a deposit a later buy depended on
      (reject), delete a deposit with no dependents (accept), 404 on bad id
- [x] `tests/services/test_money_service.py`: deposit→buy→sell→buy recycling
      — `netDeposited` stays flat while `cashAvailable` reflects recycled
      proceeds
- [x] `tests/services/test_trade_service.py` additions: buy exceeding cash
      (reject, atomic — row not inserted), editing/deleting a sell whose
      proceeds a later buy depended on (reject)

Backend — API
- [x] `api/schemas/cash.py`, `MoneySchema` in `common.py`
- [x] `DashboardResponse`/`PortfolioResponse` gain `money` (see Open Q1 on
      placement)
- [x] `api/routes/cash.py`: GET/POST `/api/cash`, DELETE `/api/cash/{id}`
- [x] `main.py`: register `cash` router; `CashValidationError` → 422,
      `CashNotFoundError` → 404 handlers (mirrors existing Trade* handlers)
- [x] `tests/routes/test_cash_route.py`: GET empty/populated, POST 201,
      POST 422 (withdraw > cash, amount ≤ 0, future date), DELETE 204/404/422
- [x] `tests/routes/test_stocks_route.py` / `test_portfolio_route.py`:
      assert `money` present and correct as a **sibling** of `summary`
      (including the case: cash deposited, zero trades → `summary: null` but
      `money` still populated); `money: null` only in the fully-empty case

## Resolution of open questions

1. **Sibling top-level field, confirmed.** `money` never nests inside
   `summary`. Cash exists independently of positions — a deposit with zero
   trades is a valid, important state and must render even when
   `hasTrades`/`summary` is null. `money` is `null` only when there is no
   cash activity and no trades at all (`has_money_activity(db)` is False).
2. **Money-in-before-money-out on same-date ties, confirmed.** Matches how
   trades actually get recorded (deposit-then-buy, sell-then-withdraw, same
   day) — rejecting that would be wrong and confusing. Made explicit in code
   (`chronological_key`'s docstring warns against "simplifying" it to
   id-order) and will be spelled out in `docs/api-contract.md` v1.5 as part
   of this phase's implementation, since it's a real business rule invented
   here (the v1.5 text as written doesn't specify tie-break behavior).
3. **Distinct, contextual wording per rejection path, confirmed** — see the
   error-message table above. No generic fallback string anywhere; every 422
   tells the user what to do next.
