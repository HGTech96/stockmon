# Phase 16 — Screener 7-day change column

## Overview

Add a "7-day change" column to the screener table, next to the existing
1-day change column. The value is already computed by `calculate_indicators`
(`indicators.change_7d_pct`, used today on the stock/screener detail pages)
but `evaluate_screener_bars` currently discards it — it just needs to be
carried through the existing pipeline: core dataclass → DB column → API
field → table column. No new core logic, no new fetch.

Null on `insufficient_history` rows (same as `rsi`/`priceVs30dAvgPct` today)
— the price-snapshot fallback only ever produces a 1-day change.

`Trend` (the up/down arrow + colored % component) currently takes a
`change1dPct`-named prop but its logic is generic; renaming that prop to
`pct` lets the new 7-day cell reuse it instead of duplicating the
up/down/flat/color logic. 3 call sites, mechanical rename.

## Files to create/change

```
api/src/stockmon/
├── core/screener.py                    (change: ScreenerEvaluation gains change_7d_pct)
├── services/screener_service.py        (change: save_screener_run writes the new column)
├── db/models.py                        (change: ScreenerResult gains change_7d_pct column)
├── api/schemas/screener.py             (change: ScreenerResultSchema gains change7dPct)
api/alembic/versions/
└── <new>_add_screener_change_7d_pct.py (new: add_column screener_results.change_7d_pct)
docs/
└── api-contract.md                     (change: v-bump, document change7dPct on GET /api/screener)
ui/src/
├── components/trend/Trend.jsx          (change: prop renamed change1dPct -> pct)
├── pages/screener/
│   ├── ScreenerRow.jsx                 (change: rename Trend prop; new 7-day cell)
│   └── ScreenerTable.jsx               (change: COLUMNS gains change7dPct entry)
├── pages/dashboard/StockRow.jsx        (change: rename Trend prop, no behavior change)
├── pages/stock-detail/DetailHeader.jsx (change: rename Trend prop, no behavior change)
└── api/types.js                        (change: ScreenerResult gains change7dPct)
```

## Schemas / interfaces

```python
# api/src/stockmon/core/screener.py
@dataclass(frozen=True)
class ScreenerEvaluation:
    ...
    change_1d_pct: Decimal | None
    change_7d_pct: Decimal | None   # new, right after change_1d_pct
    ...
```

`evaluate_screener_bars`: on the "ok" path, `change_7d_pct=indicators.change_7d_pct`
(already computed, just not returned today). On the `insufficient_history`
path, `change_7d_pct=None` (no fallback source, same as rsi today).

```python
# api/src/stockmon/db/models.py — ScreenerResult
change_7d_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
```

```python
# api/src/stockmon/api/schemas/screener.py — ScreenerResultSchema
change_7d_pct: Money | None = Field(alias="change7dPct")  # to_camel would give change7DPct
```

```
GET /api/screener — results[].change7dPct: number|null (new field)
```

```js
// ui/src/api/types.js — ScreenerResult
/** @property {number|null} change7dPct */
```

## Task list

- [x] Add `change_7d_pct` to `ScreenerEvaluation`, populate in `evaluate_screener_bars`
- [x] Alembic migration: add nullable `change_7d_pct` column to `screener_results`
- [x] `save_screener_run` writes the new field
- [x] `ScreenerResultSchema` gains `change7dPct` (aliased)
- [x] Contract v-bump documenting the new field (v1.11)
- [x] `Trend.jsx`: rename prop `change1dPct` -> `pct` (mechanical, no behavior change);
      update its 3 existing call sites (`ScreenerRow`, `StockRow`, `DetailHeader`)
- [x] `ScreenerTable.jsx`: new `change7dPct` column in `COLUMNS`, right after `change1dPct`,
      same `sortType: "number"` sortable pattern as the other numeric columns
- [x] `ScreenerRow.jsx`: new cell rendering `<Trend pct={result.change7dPct} />`
- [x] Backend test: `evaluate_screener_bars` returns `change_7d_pct` on the ok path,
      `None` on insufficient-history; full backend suite green (246 passed),
      frontend vitest suite green (43 passed)
- [x] Manual test: real dev server, confirm column renders, sorts, and matches the
      detail page's own "7-day change" indicator value for the same ticker —
      verified via a live refresh (NKE: detail page showed "7-day change -3.07%",
      table column showed the identical -3.07% after the refresh completed);
      confirmed up/down color + arrow rendering across a range of real values

## Open questions

None — this mirrors the existing 1-day-change column's plumbing exactly, just
one field further down a pipeline that already computes the value.
