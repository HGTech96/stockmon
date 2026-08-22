# Phase 10a — Fractional shares

## Overview

Allow trades in fractional share amounts (e.g. `1.25`), up to 6 decimal
places. **Sweep result: the backend already stores and computes shares as
`Decimal` end to end** (`db.models.Trade.shares` is `Numeric(12,4)`, `core`
dataclasses are `Decimal`, validation is generic `shares <= 0`) — there is no
integer type or `int()`/`round()` cast on shares anywhere in `core/`,
`services/`, or `api/`. The only real integer-shares assumptions are:

1. **DB precision**: `Numeric(12,4)` caps shares at 4 decimals; need 6.
2. **UI inputs**: both trade forms hard-code `min="1" step="1"`, which makes
   the browser reject `1.25` client-side before it ever reaches the API.
3. **UI formatting**: `fmtShares()` has no explicit `maximumFractionDigits`,
   so `Number.prototype.toLocaleString` defaults to 3 — not enough for 6.

So this phase is mostly a precision widen + two UI fixes + tests that prove
the already-Decimal core handles fractional math correctly, not a rewrite.

## Files to create/change

```
api/
├── alembic/versions/
│   └── <new>_widen_trade_shares_precision.py   (create — ALTER shares to Numeric(12,6))
├── src/stockmon/
│   └── db/models.py                            (Trade.shares: Numeric(12,4) → Numeric(12,6))
└── tests/
    ├── core/test_position.py                   (add fractional buy/sell cases)
    ├── core/test_cash.py                        (add fractional-amount cash case)
    ├── services/test_trade_service.py           (fractional buy draws exact cash)
    └── routes/test_trades_route.py              (POST accepts 1.25, rejects 0 / -1.25)

ui/src/
├── pages/portfolio/TradeModal.jsx               (shares input: step/min → fractional)
├── pages/history/EditTradeModal.jsx             (shares input: step/min → fractional)
└── lib/format.js                                (fmtShares: up to 6 decimals, no trailing zeros)

docs/api-contract.md                             (changelog line, v1.5 → v1.6)
```

No changes needed (confirmed during sweep, listed so review can verify the
sweep was real):
`core/position.py`, `core/cash.py`, `core/money.py`, `core/summary.py`,
`services/trade_service.py`, `services/cash_service.py`,
`api/schemas/trade.py`, `api/schemas/portfolio.py`, `api/schemas/stock_detail.py`,
`ui/src/api/types.js` (JSDoc already says `number`, which covers floats).

## Schemas / interfaces

```python
# db/models.py
shares: Mapped[Decimal] = mapped_column(Numeric(12, 6))   # was Numeric(12, 4)
```

```python
# alembic migration
def upgrade() -> None:
    op.alter_column(
        "trades", "shares",
        type_=sa.Numeric(precision=12, scale=6),
        existing_type=sa.Numeric(precision=12, scale=4),
    )

def downgrade() -> None:
    op.alter_column(
        "trades", "shares",
        type_=sa.Numeric(precision=12, scale=4),
        existing_type=sa.Numeric(precision=12, scale=6),
    )
```

```js
// lib/format.js
/** @param {number} n @returns {string} "1,234" or "1.25" (up to 6 decimals, no trailing zeros) */
export function fmtShares(n) {
  return n.toLocaleString("en-US", { maximumFractionDigits: 6 });
}
```

```jsx
// TradeModal.jsx / EditTradeModal.jsx — shares input
<input type="number" min="0.000001" step="any" ... />
```

## Tasks

- [x] Alembic migration: `trades.shares` → `Numeric(12, 6)`
- [x] `db/models.py`: bump `Trade.shares` column scale to match
- [x] `TradeModal.jsx`: shares input `min="0.000001" step="any"`
- [x] `EditTradeModal.jsx`: shares input `min="0.000001" step="any"`
- [x] `lib/format.js`: `fmtShares` — explicit `maximumFractionDigits: 6`
- [x] Tests — core: buy 1.25 + buy 0.75 → avg cost over 2.0 shares
- [x] Tests — core: partial sell of 0.5 from a fractional position, remaining shares/invested correct
- [x] Tests — core/service: fractional buy draws the exact correct cash amount (Decimal-exact, not rounded)
- [x] Tests — route: `POST /api/trades` accepts `shares: 1.25`; still `422` on negative/zero shares (existing coverage)
- [x] `docs/api-contract.md`: one-line changelog entry, v1.5 → v1.6 ("shares now accept up to 6 decimal places; `trades.shares` widened to `Numeric(12,6)`")
- [ ] Manual check: record a fractional buy through the UI, confirm it saves and displays with trimmed decimals (e.g. `1.25`, not `1.250000`)

## Decisions (resolved)

1. `Numeric(12,6)` confirmed — no widening beyond that.
2. Shares input keeps `min="0.000001"` as a client-side sanity guard only
   (empty/negative). `step="any"` so the browser doesn't reject any decimal
   count. Backend `shares <= 0` 422 stays the sole authority on the rule.
3. `docs/api-contract.md` header gets fixed in this phase too: bump to
   v1.6 **and** correct the stale "v1.1" in the title so the header and the
   changelog agree.
