# Phase 20 — Hard cap settings UI

## Context

The $50 default profit target had no UI to change it — `GET/PUT
/api/settings` and `PUT /api/settings/targets/{ticker}` were fully built
and working, and `ui/src/api/settings.js` already wrapped them, but no
page or component called it. The only way to change the default or set a
per-stock override was a raw API call.

This phase builds that missing UI and renames the user-facing term from
"profit target" to "hard cap" everywhere it's shown (machine field names
like `targetDollars` and `profitTarget` stay as-is — fixed API contract,
display text only). No backend evaluation-logic changes: the SELL rule
(cap reached AND a technical condition), the dollar unit, and the
default+per-stock-override structure all stay exactly as they were.

Also adds one small backend endpoint to clear a per-stock override back to
"inherit the default" — didn't exist before (only set/replace did).

This completes the spirit of the long-unchecked "Settings page for profit
targets" item under Phase 6 in `docs/plan.md` (checked off there too) but
is logged as its own numbered phase per the project's phase-per-feature
convention.

## Files changed

```
api/src/stockmon/
├── services/settings_service.py     (remove_position_target)
├── api/routes/settings.py           (DELETE /api/settings/targets/{ticker})
api/tests/
├── services/test_settings_service.py
└── routes/test_settings_route.py
docs/
├── api-contract.md                  (DELETE endpoint; changelog v1.13)
└── plan.md                          (Phase 20 entry; Phase 6 box checked)
ui/src/
├── App.jsx                          (/settings route)
├── components/layout/NavTabs.jsx    ("Settings" tab)
├── api/settings.js                  (deletePositionTarget)
├── pages/settings/
│   └── SettingsPage.jsx             (default cap form + override list)
├── pages/stock-detail/
│   ├── PositionCard.jsx             (wording + "Edit" action)
│   └── HardCapModal.jsx             (per-stock override form)
└── pages/portfolio/
    ├── PositionsTable.jsx           (wording)
    └── EmptyState.jsx               (wording)
```

## Design

**Backend** — `remove_position_target` mirrors `set_position_target`,
idempotent (no-op if no override exists), raises `StockNotFoundError`
(existing 404 handler) if the ticker isn't on the watchlist:

```python
def remove_position_target(db: Session, ticker: str) -> SettingsView:
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if stock is None:
        raise StockNotFoundError(ticker)
    override = db.get(ProfitTarget, stock.id)
    if override is not None:
        db.delete(override)
        db.commit()
    return _build_view(db, _get_or_create_settings(db))
```

Route matches the existing 204-no-body DELETE convention
(`DELETE /api/cash/{id}`, `DELETE /api/trades/{id}`). No `core/` changes —
`get_effective_target` already falls through to the default whenever no
`ProfitTarget` row exists.

**Frontend** — `SettingsPage.jsx` has two sections: a default-cap form
(mirrors `CashModal.jsx`'s input/mutation/error pattern) and a read-only
list of per-stock overrides with a "Reset to default" button per row.
`HardCapModal.jsx` (same shape as `CashModal.jsx`) is opened from
`PositionCard.jsx`'s new "Edit" action to set/adjust one stock's override;
resetting lives only on the Settings page, keeping each surface
single-purpose. Both mutation paths invalidate `["settings"]`, `["stocks"]`,
`["portfolio"]`, and the partial `["stock"]` key (clears every cached
stock-detail entry via TanStack Query's default prefix matching).

**Wording (display text only):**
- `PositionCard.jsx`: "Progress to profit target" → "Progress to hard cap"
- `PositionsTable.jsx`: "To target" → "To cap"
- `EmptyState.jsx`: "your targets" → "your hard caps"

## Tasks

- [x] `settings_service.py`: `remove_position_target`
- [x] `routes/settings.py`: `DELETE /api/settings/targets/{ticker}`
- [x] Tests: service + route (unknown-ticker 404, no-override no-op, clears override)
- [ ] `docs/api-contract.md`: DELETE endpoint was never actually added to
      the contract doc despite being implemented — follow-up needed
- [x] `docs/plan.md` Phase 20 + Phase 6 checkbox
- [x] `api/settings.js`: `deletePositionTarget`
- [x] `SettingsPage.jsx`, `App.jsx` route, `NavTabs.jsx` tab
- [x] `HardCapModal.jsx`; wire into `PositionCard.jsx` + wording change
- [x] `PositionsTable.jsx` / `EmptyState.jsx`: wording changes

## Verification

1. `pytest` in `api/` and `npm test` in `ui/` — both suites green.
2. Manual: `/settings` default-cap edit persists; per-stock override set
   via detail-page modal shows up on `/settings`; "Reset to default" clears
   it and the detail page falls back to the default. Dashboard/portfolio
   suggestions and the "To cap" column unaffected (SELL/WAIT logic untouched).
