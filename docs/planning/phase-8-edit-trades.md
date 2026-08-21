# Phase 8 — Edit / Delete Trades

## Overview

Add `PUT /api/trades/{id}` and `DELETE /api/trades/{id}` (contract v1.4,
already documented in `docs/api-contract.md`). Both mutate one trade and
must leave every trade for that ticker satisfying the same rule
`derive_position` already enforces: replayed in date order, cumulative
sells never exceed cumulative shares held at that point.

**Design decision: no new core function.** `derive_position` already *is*
the full-sequence validator — it raises `PositionError` the instant a
replayed sell exceeds shares held, whatever produced the trade list. Adding
a second function that re-implements the same replay/oversell check would
violate the "every business rule exists in exactly ONE core function" rule
in CLAUDE.md. Instead, the service layer builds the hypothetical
post-edit / post-delete event list for the affected ticker and feeds it to
the existing `derive_position` — validation and the recalculated position
come out of the same call, atomically, before anything touches the DB.

Reordering falls out for free: trade rows are loaded pre-sorted by
`(trade_date, id)`, the edited entry's value is swapped in-place, and a
stable `list.sort(key=lambda e: e.date)` relocates only that entry —
everything else keeps its original relative order.

Backend: shared field-validation helper (extracted from `record_trade`,
reused by the new `update_trade`) → `update_trade` / `delete_trade` in
`trade_service.py` → thin PUT/DELETE routes → a `TradeNotFoundError` +
global exception handler, mirroring the existing `StockNotFoundError`
pattern in `main.py`. Frontend: edit/delete icons per history row, an edit
modal, and a confirm dialog (no delete/confirm pattern exists anywhere in
the UI yet — this introduces the first one).

## Files to create/change

```
api/src/stockmon/
  core/position.py                    (no changes — derive_position reused as-is)
  services/trade_service.py           (add: _validate_trade_fields, TradeNotFoundError,
                                        update_trade, delete_trade;
                                        refactor: record_trade uses _validate_trade_fields;
                                        add: _load_trade_rows helper)
  api/schemas/trade.py                (add: TradeUpdateRequest)
  api/routes/trades.py                (add: PUT /api/trades/{id}, DELETE /api/trades/{id})
  main.py                             (add: TradeNotFoundError exception handler)
api/tests/
  core/test_position.py               (add: sequence-validation cases via derive_position,
                                        simulating edit/delete inputs)
  services/test_trade_service.py      (add: update_trade / delete_trade cases)
  routes/test_trades_route.py         (add: PUT/DELETE cases)

ui/src/
  api/trades.js                       (add: putTrade, deleteTrade)
  api/types.js                        (add: TradeUpdateRequest)
  pages/history/
    HistoryPage.jsx                   (add: edit/delete modal state + mutations)
    TradeHistoryTable.jsx             (add: Actions column header)
    TradeHistoryRow.jsx               (add: edit/delete icon buttons)
    EditTradeModal.jsx                (new)
    DeleteTradeConfirm.jsx            (new)
  pages/portfolio/TradeModal.jsx      (fix: invalidate ["trades"] too on add — see open Q1)
```

## Schemas / interfaces

**services/trade_service.py**:

```python
class TradeNotFoundError(Exception):
    pass


def _validate_trade_fields(shares: Decimal, price_per_share: Decimal, trade_date: date) -> None:
    """Shared by record_trade and update_trade — the one place these three
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


def update_trade(
    db: Session, trade_id: int, shares: Decimal, price_per_share: Decimal, trade_date: date
) -> TradeResult:
    """Ticker and action are immutable. Builds the full post-edit event list
    for the trade's ticker, validates it via derive_position (raises
    TradeValidationError on oversell), and only then mutates the row —
    never a partial apply."""


def delete_trade(db: Session, trade_id: int) -> Position | None:
    """Builds the event list for the ticker with this trade removed,
    validates via derive_position, then deletes. Returns the recalculated
    position (None if the deletion leaves the ticker fully closed / never
    opened)."""
```

**api/schemas/trade.py**:

```python
class TradeUpdateRequest(CamelModel):
    shares: Decimal
    price_per_share: Decimal
    date: date
```

PUT response reuses the existing `TradeResponse` (`trade` + `updatedPosition`)
— identical shape to POST's response, per contract.

**api/routes/trades.py**:

```python
@router.put("/api/trades/{id}", response_model=TradeResponse)
def edit_trade(id: int, body: TradeUpdateRequest, db: Session = Depends(get_db)) -> TradeResponse:
    result = update_trade(db, id, body.shares, body.price_per_share, body.date)
    return TradeResponse.from_core(result.trade.stock.ticker, result)


@router.delete("/api/trades/{id}", status_code=204)
def remove_trade(id: int, db: Session = Depends(get_db)) -> None:
    delete_trade(db, id)
```

**main.py** (new handler, same shape as the existing `StockNotFoundError` one):

```python
@app.exception_handler(TradeNotFoundError)
def handle_trade_not_found_error(request: Request, exc: TradeNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": str(exc)})
```

**ui/src/api/trades.js**:

```js
/** @param {number} id @param {import('./types').TradeUpdateRequest} payload */
export function putTrade(id, payload) {
  return request(`/trades/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

/** @param {number} id */
export function deleteTrade(id) {
  return request(`/trades/${id}`, { method: "DELETE" });
}
```

## Tasks

Backend
- [x] Extract `_validate_trade_fields`; `record_trade` calls it (no behavior change)
- [x] `_load_trade_rows` helper; `_load_trade_events` becomes a thin wrapper over it
- [x] `TradeNotFoundError` + `update_trade` + `delete_trade` in `trade_service.py`
- [x] Tests in `test_position.py` (via `derive_position`, simulating edit/delete inputs):
      edit a buy down below a later sell's need (reject), move a trade's
      date to reorder the sequence and make it invalid (reject at new
      position), delete a buy a later sell depends on (reject), valid edit
      accepted, valid delete accepted, edit that closes then correctly
      reopens a position (accept, correct reset avg price)
- [x] Tests in `test_trade_service.py`: update_trade success (recalculated
      position correct), update_trade 404 (bad id), update_trade 422
      (oversell) leaves DB row unchanged (atomicity check), delete_trade
      success (position recalculated / null when fully closed), delete_trade
      404, delete_trade 422 leaves row in place
- [x] `TradeUpdateRequest` schema; PUT/DELETE routes
- [x] `TradeNotFoundError` exception handler in `main.py`
- [x] Route tests: PUT 200/422/404 (key sets + camelCase), DELETE 204/422/404

Frontend
- [x] `putTrade` / `deleteTrade` in `api/trades.js`; `TradeUpdateRequest` typedef
- [x] `EditTradeModal.jsx`: mirrors `TradeModal.jsx`'s hand-rolled style
      (same field classes, disable-while-pending, inline 422 message) —
      ticker shown as read-only text, not an input; shares/price/date
      editable, pre-filled from the row
- [x] `DeleteTradeConfirm.jsx`: states the downstream effect ("This changes
      your {TICKER} position and may affect later trades."); Cancel/Delete
      buttons disabled while pending; shows inline 422 if the delete is
      rejected (dependent sell)
- [x] `TradeHistoryTable.jsx` / `TradeHistoryRow.jsx`: Actions column with
      edit (pencil) and delete (trash) icon buttons per row
- [x] `HistoryPage.jsx`: owns which-row-is-being-edited/deleted state, wires
      both mutations, invalidates `["trades"]`, `["stocks"]`, `["portfolio"]`
      on success for both
- [x] Fix `TradeModal.jsx`'s `postTrade` success handler to also invalidate
      `["trades"]` (currently only invalidates `["stocks"]`/`["portfolio"]`,
      so an added trade doesn't refresh an already-open History page)
- [x] Manual check: added a throwaway MSFT trade via the API, edited its
      shares in the UI (table + total updated live via query invalidation),
      deleted it via the confirm dialog (row disappeared, count updated),
      then reproduced the oversell case (buy 5 + sell 4, edit the buy down
      to 2) and confirmed the exact backend 422 message ("cannot sell
      4.0000 shares on 2026-01-10, only 2 held") renders inline in the edit
      modal with the underlying row left unchanged. Test trades removed
      afterward; real trade history (8 trades) unaffected. Also confirmed
      `res.status === 204` handling was needed in `api/client.js` — DELETE
      was the first no-body response the shared `request()` helper had to
      handle; `res.json()` on an empty 204 body throws, so this was a
      necessary small addition beyond the original schema, not scope creep.
      `poetry run pytest` (150 passed), `npm run build` and `npm run lint`
      both clean.

## Open questions

1. While in `TradeModal.jsx` for this phase's query-invalidation work, I
   noticed its existing `postTrade` success handler invalidates only
   `["stocks"]` and `["portfolio"]` — not `["trades"]`. So adding a trade
   today doesn't refresh an already-open History page. Fix it alongside
   this phase (one-line addition), or leave it out of scope?
2. No confirm-dialog pattern exists anywhere in the UI yet, and there are
   two divergent primitives available: the unused shadcn-style
   `Dialog`/`DialogFooter`/`Button` components, vs. `TradeModal.jsx`'s
   actual hand-rolled `<button>` styling. Plan assumes matching
   `TradeModal.jsx`'s established (if divergent) convention for both new
   modals — confirm, or would you rather this phase adopt the shadcn
   primitives instead?
3. `PUT` re-validates shares > 0, price > 0, and date-not-in-future (same
   as `POST`) even though the contract text only spells out the
   sequence-oversell 422. Confirm these basic field checks should still
   apply on edit.

## Resolution of open questions

1. **In scope.** Same bug class this phase exists to prevent (stale views
   after a write); one-line fix. Added as a task above:
   `TradeModal.jsx`'s `postTrade` success handler now also invalidates
   `["trades"]`.
2. **Match `TradeModal.jsx`'s hand-rolled convention** for `EditTradeModal.jsx`
   and `DeleteTradeConfirm.jsx` — consistency within the app over
   introducing a second primitive mid-project. **Tech debt, logged, not
   fixed this phase:** the app has two divergent modal/dialog approaches —
   the shadcn-style `Dialog`/`DialogFooter`/`Button` primitives in
   `components/ui/`, currently unused by any page, and `TradeModal.jsx`'s
   hand-rolled inline-Tailwind style, which is what's actually used and
   what this phase extends. A future cleanup should either adopt the
   shadcn primitives app-wide (rewriting `TradeModal.jsx` too) or delete
   the unused `ui/` components — a conscious choice, not left to drift.
3. **Confirmed.** PUT applies the same basic field validation as POST
   (shares > 0, price > 0, date not in the future) via the shared
   `_validate_trade_fields` helper. `docs/api-contract.md`'s v1.4 PUT spec
   updated with a line making this explicit (it previously only spelled
   out the sequence-oversell rule, which was underspecified).
