# Phase 7 — Trade History

## Overview

Add `GET /api/trades` (contract v1.2, already documented) and a History page
that lists every recorded trade newest-first, with realized P/L on sells.
Realized P/L needs a new pure core function that replays trades per-stock
using the same weighted-average-cost rule as `derive_position`, capturing
the average cost at the moment of each sale instead of discarding it.

Backend: core function + tests → service query (joins trades across all
stocks, groups per-ticker for the replay, re-sorts newest-first) → thin
route/schema. Frontend: new page + nav tab, reusing existing table/format/
badge patterns from the Portfolio page — no new formatting helpers needed.

## Files to create/change

```
api/src/stockmon/
  core/position.py                    (add: compute_realized_pnl)
  services/trade_service.py           (add: TradeHistoryEntry, list_trade_history)
  api/schemas/trade.py                (add: TradeHistoryEntrySchema, TradeHistoryResponse)
  api/routes/trades.py                (add: GET /api/trades)
api/tests/
  core/test_position.py               (add: compute_realized_pnl cases)
  services/test_trade_service.py      (add: list_trade_history cases)
  routes/test_trades_route.py         (add: GET /api/trades cases)
  conftest.py                         (add: make_trade helper — see open question)

ui/src/
  App.jsx                             (add: /history route)
  components/layout/NavTabs.jsx       (add: History tab)
  components/badge/ActionBadge.jsx    (new: buy/sell pill, green/orange)
  api/types.js                        (add: TradeHistoryEntry, TradesResponse)
  api/trades.js                       (add: getTrades)
  pages/history/
    HistoryPage.jsx                   (new)
    TradeHistoryTable.jsx             (new)
    TradeHistoryRow.jsx               (new)
    EmptyState.jsx                    (new)
```

## Schemas / interfaces

**core/position.py** — sibling to `derive_position`, same replay pattern,
same input contract (caller sorts chronologically):

```python
def compute_realized_pnl(trades: list[TradeEvent]) -> list[Decimal | None]:
    """Parallel list to `trades`: for each sell, (sale price - avg cost at
    that point in the replay) * shares sold. None for buys."""
```

**services/trade_service.py**:

```python
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

def list_trade_history(db: Session) -> list[TradeHistoryEntry]:
    """Loads all trades + stocks, groups by stock_id, runs
    compute_realized_pnl per group (chronological), then returns entries
    sorted newest-first (date desc, id desc) across all tickers."""
```

**api/schemas/trade.py** (mirrors `PortfolioResponse`'s meta+list shape):

```python
class TradeHistoryEntrySchema(CamelModel):
    id: int
    ticker: str
    company_name: str
    action: Literal["buy", "sell"]
    shares: Money
    price_per_share: Money
    total_usd: Money
    realized_pnl_usd: Money | None
    date: date

class TradeHistoryResponse(CamelModel):
    meta: MetaSchema
    trades: list[TradeHistoryEntrySchema]
```

**api/routes/trades.py**:

```python
@router.get("/api/trades", response_model=TradeHistoryResponse)
def list_trades(db: Session = Depends(get_db)) -> TradeHistoryResponse:
    meta = MetaSchema.from_core(get_freshness(db))
    entries = list_trade_history(db)
    return TradeHistoryResponse(meta=meta, trades=[TradeHistoryEntrySchema.from_core(e) for e in entries])
```

**ui/src/api/types.js**:

```js
/**
 * @typedef {Object} TradeHistoryEntry
 * @property {number} id
 * @property {string} ticker
 * @property {string} companyName
 * @property {"buy"|"sell"} action
 * @property {number} shares
 * @property {number} pricePerShare
 * @property {number} totalUsd
 * @property {number|null} realizedPnlUsd
 * @property {string} date
 */

/**
 * @typedef {Object} TradesResponse
 * @property {Meta} meta
 * @property {TradeHistoryEntry[]} trades
 */
```

## Tasks

Backend
- [x] `compute_realized_pnl` in `core/position.py`
- [x] Tests in `test_position.py`: single sell profit, single sell loss,
      multiple partial sells at different avg costs (interleaved buys),
      position closed then reopened then sold again
- [x] `TradeHistoryEntry` + `list_trade_history` in `services/trade_service.py`
- [x] Tests in `test_trade_service.py`: multi-ticker ordering (newest first),
      companyName/totalUsd correctness, realizedPnlUsd null on buys
- [x] `TradeHistoryEntrySchema` + `TradeHistoryResponse` in `api/schemas/trade.py`
- [x] `GET /api/trades` route in `api/routes/trades.py`
- [x] Route tests: empty list, populated list, key sets, camelCase fields

Frontend
- [x] `getTrades()` in `api/trades.js`; typedefs in `api/types.js`
- [x] `ActionBadge` component (buy=green/good, sell=orange/warn, per fixed
      badge-color rule)
- [x] `HistoryPage.jsx`: `useQuery(["trades"], getTrades)`, meta wiring via
      `setMeta`, loading/error states (copy `PortfolioPage.jsx` pattern),
      empty state when `trades.length === 0`
- [x] `TradeHistoryTable.jsx` + `TradeHistoryRow.jsx`: columns date, stock,
      action (badge), shares, price, total, realized P/L (colored
      green/red via `fmtMoneySigned`, dash on buys) — same table
      shell/classes as `PositionsTable`/`PositionRow`
- [x] `EmptyState.jsx` for History (no CTA button — trades are added from
      the Portfolio page)
- [x] Route + nav tab in `App.jsx` / `NavTabs.jsx`
- [x] Manual check: `npm run build`/`lint` clean, viewed `/history` in
      Chrome against the real dev DB (13 stocks, 5 buy trades) — nav tab,
      freshness bar, table, and buy badges all render correctly. Didn't
      insert a test sell trade into the real DB just for a screenshot;
      sell/realized-P/L rendering is covered by the passing backend tests
      instead.

## Resolution of open questions

1. **`compute_realized_pnl` duplication**: implemented as a self-contained
   sibling function to `derive_position` (small ~10-line duplication of the
   replay loop), matching the existing `_load_trade_events` duplication
   pattern already in the codebase. No objection raised — kept as planned.
2. **`make_trade` conftest helper**: not needed — `test_trade_service.py`'s
   existing convention builds up trade history via `record_trade(...)`
   calls rather than raw `Trade(...)` inserts, so the new
   `list_trade_history` tests reuse that pattern directly with no new
   fixture.
