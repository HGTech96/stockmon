# Phase 21 — Per-stock analysis note

## Context

Adds a personal "analysis" record per tracked stock: a date and a value the
user records from their own research. Nullable (most stocks will have none),
one per stock, freely editable/overwritable. Applies to any stock on the
watchlist regardless of ownership — unlike the hard cap (Phase 20), which is
only meaningful for owned positions, this is a standalone note.

Purely stored/displayed data — per CLAUDE.md's "no black-box scoring" rule,
it does NOT feed into the BUY/WAIT/SELL suggestion logic.

## Files to create/change

```
api/src/stockmon/
├── db/models.py                       (Stock: + analysis_date, analysis_value)
├── alembic/versions/
│   └── <rev>_add_stock_analysis.py    (new migration)
├── services/
│   ├── stock_service.py               (set_analysis, clear_analysis)
│   └── stock_detail_service.py        (thread analysis into StockDetail)
├── api/
│   ├── schemas/stock_detail.py        (AnalysisSchema; field on StockDetailResponse)
│   └── routes/stocks.py               (PUT/DELETE /api/stocks/{ticker}/analysis)
api/tests/
├── services/test_stock_service.py
├── services/test_stock_detail_service.py
└── routes/test_stocks_route.py
docs/
├── api-contract.md                    (new endpoint + field, version bump)
└── plan.md                            (Phase 21 entry, after approval)
ui/src/
├── api/
│   └── stocks.js                      (setAnalysis, clearAnalysis)
└── pages/stock-detail/
    ├── StockDetailPage.jsx            (render AnalysisCard)
    ├── AnalysisCard.jsx               (date + value, or "No analysis recorded"; Edit/Clear)
    └── AnalysisModal.jsx              (date + value form, mirrors HardCapModal.jsx)
```

## Schema

**DB** (`stocks` table, nullable columns — not a separate override table,
since there's no default to fall back to):

```python
analysis_date: Mapped[date | None] = mapped_column(Date)
analysis_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
```

**API** — new block on `GET /api/stocks/{ticker}`, null when unset:

```json
"analysis": { "date": "2026-08-20", "value": 210.00 }
```

`PUT /api/stocks/{ticker}/analysis`

```json
{ "date": "2026-08-20", "value": 210.00 }
```
→ `200` with the updated `analysis` block. `404` if ticker isn't on the watchlist.

`DELETE /api/stocks/{ticker}/analysis` → clears back to `null`, `204`.

## Tasks

- [x] Migration: `stocks.analysis_date`, `stocks.analysis_value` (nullable)
- [x] `db/models.py`: add the two columns
- [x] `stock_service.py`: `set_analysis(db, ticker, date, value)`, `clear_analysis(db, ticker)` (reuse `StockNotFoundError`)
- [x] `stock_detail_service.py`: include analysis in the `StockDetail` dataclass
- [x] `schemas/stock_detail.py`: `AnalysisSchema`, `analysis` field on `StockDetailResponse`
- [x] `routes/stocks.py`: `PUT`/`DELETE /api/stocks/{ticker}/analysis`
- [x] Tests: service + route (set, overwrite, clear, unknown-ticker 404, null-by-default)
- [x] `docs/api-contract.md` version bump (v1.14, later renumbered to
  v1.14/v1.15 after resolving a v1.13 collision with Phase 20's DELETE
  settings endpoint doc); `docs/plan.md` Phase 21 entry
- [x] `ui/api/stocks.js`: `putAnalysis`, `deleteAnalysis`
- [x] `AnalysisCard.jsx` + `AnalysisModal.jsx`; wired into `StockDetailPage.jsx` for owned AND unowned stocks
- [x] Invalidate `["stock"]` query on save/clear

## Open questions

1. **What is "value"?** A dollar price target from your own valuation (plan
   assumes this — `Numeric(12,4)`, shown like other money fields), a
   rating/score, or free text? This changes the column type and formatting.
2. **Display scope** — detail page only, or also a column/indicator on the
   dashboard and portfolio tables?
3. Confirm: purely a personal note, no effect on suggestion logic — correct?
4. Endpoint shape — separate `PUT`/`DELETE /api/stocks/{ticker}/analysis`
   (mirrors the settings/targets pattern), or fold into a broader stock-edit
   endpoint if one's coming later anyway?

Resolved (2026-08-28): value = dollar price target, shown with its date;
detail page only; no effect on suggestion logic.

## Addendum — "Progress to analysis" bar

Mirrors the hard-cap progress bar (`PositionCard.jsx`): a 0-100% bar showing
how close `currentPrice` is to the analyzed target price. Hidden entirely
when there's no analysis value, and also hidden (not zero/broken) when
`currentPrice` isn't known yet (e.g. a stock that's never been refreshed).

**Backend** — new pure function, `core/analysis.py` (separate from
`core/position.py` since it's independent of ownership/positions):

```python
@dataclass(frozen=True)
class AnalysisProgress:
    target_price: Decimal
    progress_price: Decimal
    remaining_price: Decimal
    reached: bool

def evaluate_analysis_progress(current_price: Decimal, target_price: Decimal) -> AnalysisProgress:
    ...  # same capped/uncapped shape as evaluate_profit_target
```

`stock_detail_service.py` computes it when `analysis` is set AND
`evaluation.current_price is not None`; `StockDetail` gains `analysis_progress`.
`screener_detail_service.py` passes `analysis_progress=None` (screener
tickers are never on the watchlist).

**API** — `analysis.progress` sub-block on `GET /api/stocks/{ticker}` only
(contract v1.15); `null` when `currentPrice` is unknown. NOT added to the
`PUT`/`DELETE /api/stocks/{ticker}/analysis` responses — the UI re-fetches
detail on save/clear (existing `["stock"]` invalidation), same as hard cap.

**Frontend** — `AnalysisCard.jsx` renders the bar (same markup/classes as
`PositionCard.jsx`'s hard-cap bar: `h-2 rounded-pill` track, `fmtToGo` for
the caption) only when `analysis.progress` is truthy.

- [x] `core/analysis.py`: `AnalysisProgress` + `evaluate_analysis_progress` (+ tests)
- [x] `stock_detail_service.py` / `screener_detail_service.py`: thread `analysis_progress`
- [x] `schemas/stock_detail.py`: `AnalysisProgressSchema`, `DetailAnalysisSchema` (nests `progress`)
- [x] `docs/api-contract.md` v1.15
- [x] `AnalysisCard.jsx`: "Progress to analysis" bar, hidden when no analysis or no current price
- [x] Verified live: below-target and reached-target states, both owned and unowned tickers
