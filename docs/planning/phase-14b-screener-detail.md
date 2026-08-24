# Phase 14b — Screener live-fetch detail endpoint

## Overview

`GET /api/screener/{ticker}/detail` — full stock detail for any ticker,
computed from a live fetch at request time (nothing persisted). Contract
is already fixed in `docs/api-contract.md` (v1.8): the response shape is
**identical to the tracked, unowned-stock detail response** (`position`
always null, `chart.userAvgPurchasePrice` always null, `suggestion.type`
always `"entry"`). Because the shapes are identical, this reuses the
existing `StockDetail` dataclass and `StockDetailResponse` schema
unchanged — the new code only *produces* a `StockDetail` from a live
fetch instead of from the DB.

No position, cash, or exit logic — screener tickers are never owned
(per CLAUDE.md's screener rules).

## Files to create/change

```
api/src/stockmon/services/
├── stock_detail_service.py      (change: export news-links helper)
└── screener_detail_service.py   (new: live-fetch detail builder)

api/src/stockmon/api/routes/
└── screener.py                  (change: add GET .../{ticker}/detail)

api/tests/services/
└── test_screener_detail_service.py   (new)

api/tests/routes/
└── test_screener_detail_route.py     (new)
```

No schema changes — `StockDetailResponse` (`api/src/stockmon/api/schemas/stock_detail.py`)
is reused as-is.

## Interfaces

```python
# stock_detail_service.py — rename _news_links -> news_links_for_ticker,
# taking the ticker + optional IR url directly instead of a Stock row,
# so screener_detail_service can share it without a persisted Stock.
def news_links_for_ticker(ticker: str, investor_relations_url: str | None) -> NewsLinks: ...


# screener_detail_service.py
def get_screener_stock_detail(
    provider: MarketDataProvider, ticker: str
) -> StockDetail:
    """Live-fetch one ticker's history (same DEFAULT_HISTORY_DAYS fetch the
    screener job uses) and build the same StockDetail shape stock_detail_service
    builds from the DB. No DB reads/writes; no position (screener stocks are
    never owned).

    Raises UnknownTickerError (-> 422, existing handler) if the ticker's
    company name can't be resolved. A resolvable ticker with too little
    price history (or a history fetch failure) is NOT an error -- it's the
    ordinary insufficient_history status, same as a freshly-added tracked
    stock with no bars yet.
    """
```

Route addition (`screener.py`):

```python
@router.get("/api/screener/{ticker}/detail", response_model=StockDetailResponse)
def get_screener_detail(
    ticker: str,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> StockDetailResponse:
    meta = MetaSchema.from_core(get_freshness(db))  # same freshness meta as GET /api/screener
    detail = get_screener_stock_detail(provider, ticker)
    return StockDetailResponse.from_core(meta, detail)
```

## Design notes

- **Ticker resolution** mirrors `add_stock_to_watchlist`: resolve company
  name via `provider.fetch_company_name`; a raised `MarketDataError` or a
  blank name raises the existing `UnknownTickerError` (already wired to
  422 in `main.py` — no new exception handler needed).
- **History fetch**: `provider.fetch_daily_history(ticker, DEFAULT_HISTORY_DAYS)`
  — same constant the screener job imports from `refresh_service`. If this
  raises `MarketDataError` (zero bars — YFinanceProvider's empty-history
  case), treat it as `bars = []` and fall into the insufficient-history
  path, rather than a 422 — the ticker itself is real (name resolved), it
  just has no usable price data yet, same class of state a newly-tracked
  stock can be in.
- **Indicators/evaluation**: call the same core functions the DB-backed
  path uses directly — `calculate_indicators` / `calculate_price_snapshot`
  (`core/indicators.py`) for the ok/insufficient_history branch,
  `evaluate_entry` (not `evaluate_stock`, since there's no position — this
  IS what `evaluate_stock` reduces to when `position_value` is None, but
  calling `evaluate_entry` directly makes "no exit logic here" explicit)
  and `detect_sharp_move` (`core/evaluation.py`). No indicator/evaluation
  logic is reimplemented.
- **Building the `StockDetail`**: construct an **unpersisted** `Stock(ticker=..., company_name=...)`
  instance (never `db.add`-ed or committed) purely to satisfy the existing
  `StockEvaluation.stock` / `StockDetail` shape — `position` and
  `position_value` are always `None`. This is what makes reusing
  `StockDetailResponse.from_core` unchanged possible.
- **`effective_target_dollars`**: `StockDetail` requires this field, but
  it's only read from `detail.profit_target`, which is always `None` here
  (no position). Passed as `Decimal(0)` with a short comment — dead value,
  not worth threading `Optional` through a shared dataclass for one caller.
- **News links**: screener tickers have no `investor_relations_url` (not
  a DB row), so `news_links_for_ticker(ticker, None)` always yields
  `investorRelations: null`.

## Tasks

- [x] Rename `stock_detail_service._news_links` -> `news_links_for_ticker(ticker, investor_relations_url)`, update its one call site in `get_stock_detail`
- [x] Add `screener_detail_service.py` with `get_screener_stock_detail`
- [x] Add `GET /api/screener/{ticker}/detail` route in `screener.py`
- [x] Service tests: valid unowned ticker -> full `StockDetail` (position/user_avg_purchase_price None, chart populated); insufficient-history ticker (short + zero-bar history) -> status + trading_days_until_ready; unresolved ticker -> `UnknownTickerError`
- [x] Route tests (`FakeProvider`, same pattern as `test_stocks_route.py`): 200 full unowned shape (`position: null`, `chart.userAvgPurchasePrice: null`, `suggestion.type: "entry"`); 422 unknown ticker; insufficient-history state
- [x] Mark this section's checkboxes done in `docs/plan.md`

## Open questions

None — contract, error modes, and reuse points are all pinned down by the
existing contract text and the Phase 5a/14a code this mirrors.
