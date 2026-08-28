# Phase 18 — Live intraday current price

## Context

`currentPrice` was previously sourced only from `fetch_daily_history()`
(yfinance `.history()`). Its last bar is sometimes an in-progress "today"
row (updates during market hours) and sometimes a stale prior close —
purely by accident of when a refresh happens to run, not a real live-quote
feature.

`MarketDataProvider.fetch_current_quote(ticker) -> Quote` already existed in
`core/market_data.py` and was fully implemented in `YFinanceProvider` (uses
yfinance's `fast_info["last_price"]`, closer to a true real-time price) —
but was never called anywhere. Dead scaffolding.

The app's architecture is refresh-then-read: GETs only read from the DB;
`POST /api/refresh` (and its screener/add-stock siblings) is the only place
live data enters the system. So "live" here means "as of your last
refresh," not "live on every page view" — matching the existing pull-only,
no-websockets design.

The fix: wire the existing `fetch_current_quote` into the refresh path so
the most recent bar's close reflects the live quote when it's today's
session. No API contract shape changes — `currentPrice` is already on the
wire everywhere; only its computed value gets more accurate during market
hours.

## Files changed

```
api/src/stockmon/
├── core/
│   └── market_data.py          (merge_live_quote pure function)
├── services/
│   ├── refresh_service.py      (overlay_live_price; called in refresh_stock)
│   ├── screener_service.py     (overlay_live_price in fetch_and_evaluate_ticker)
│   └── screener_detail_service.py  (overlay_live_price in get_screener_stock_detail)
api/tests/
├── core/
│   └── test_market_data.py     (unit tests for merge_live_quote)
└── services/
    ├── test_refresh_service.py         (FakeProvider extended + new tests)
    ├── test_screener_service.py        (FakeProvider extended + new tests)
    └── test_screener_detail_service.py (FakeProvider extended + new tests)
docs/
├── plan.md                     (Phase 18 checklist entry)
└── api-contract.md             (clarifying note under currentPrice)
```

## Design

**Pure merge logic — `core/market_data.py`:**

```python
def merge_live_quote(bars: list[DailyBar], quote: Quote) -> list[DailyBar]:
    """Replaces the most recent bar's close with a live quote when that bar
    is the same trading day as the quote -- lets callers show a live
    intraday price instead of the last completed daily close. No-op when
    there's no bar for the quote's day (market not yet in session)."""
    if not bars or bars[-1].date != quote.as_of.date():
        return bars
    return [*bars[:-1], replace(bars[-1], close=quote.price)]
```

**I/O wrapper — `services/refresh_service.py`:**

```python
def overlay_live_price(provider: MarketDataProvider, ticker: str, bars: list[DailyBar]) -> list[DailyBar]:
    """Fetches a live quote and overlays it onto today's bar via
    merge_live_quote, so currentPrice reflects the live price rather than
    the last completed close. A quote-fetch hiccup falls back to the
    unmodified bars -- valid daily history should never be discarded over it."""
    if not bars or bars[-1].date != date.today():
        return bars
    try:
        quote = provider.fetch_current_quote(ticker)
    except MarketDataError:
        return bars
    return merge_live_quote(bars, quote)
```

Called right after every existing `provider.fetch_daily_history(...)` call:
- `refresh_service.refresh_stock` — before `upsert_daily_prices`. Covers the
  dashboard's `POST /api/refresh` **and** `add_stock_to_watchlist`.
- `screener_service.fetch_and_evaluate_ticker` — before `evaluate_screener_bars`.
- `screener_detail_service.get_screener_stock_detail` — after the
  fetch-or-`[]` block (no-op automatically when `bars == []`).

**Why this shape:**
- Pure replace-logic lives once in `core/`, tested without any provider/DB.
- The service-level gate (`bars[-1].date != date.today(): return bars`)
  avoids firing a needless extra yfinance call outside market hours/weekends.
- A quote failure degrades gracefully (keeps the good daily-history price)
  rather than failing a refresh that otherwise succeeded.
- No new field, no contract version bump.

**Known limitations:**
- Still not push/real-time — "live as of your last refresh."
- `fast_info["last_price"]` is Yahoo's free-tier quote, same delay/reliability
  caveats as the rest of this app's yfinance usage.
- One extra yfinance call per ticker per refresh — negligible for the
  ~16-stock watchlist, roughly doubles per-ticker calls for the ~150-ticker
  screener batch. `BATCH_SIZE`/`BATCH_PAUSE_SECONDS` in `screener_service.py`
  are tunable if this causes rate-limiting.

## Tasks

- [x] `core/market_data.py`: add `merge_live_quote(bars, quote)` pure function
- [x] `api/tests/core/test_market_data.py`: unit tests — same-day quote
      replaces close; no bars → no-op; last bar not quote's day → no-op
- [x] `services/refresh_service.py`: add `overlay_live_price`; wired into
      `refresh_stock` before `upsert_daily_prices`
- [x] `services/screener_service.py`: wired into `fetch_and_evaluate_ticker`
- [x] `services/screener_detail_service.py`: wired into `get_screener_stock_detail`
- [x] Extended each test file's local `FakeProvider` with fakeable
      `fetch_current_quote` (success + `MarketDataError`) and added tests:
      override, fallback-on-failure, no-quote-call-for-non-today-bar
- [x] `docs/plan.md`: Phase 18 entry
- [x] `docs/api-contract.md`: clarifying line under `currentPrice`
- [x] `pytest` full suite green
- [ ] Manual verification during live market hours (see below) — pending,
      run this next time the market is open

## Verification

1. `pytest` in `api/` — new + existing tests green (existing tests use fixed
   non-today dates, so they hit the no-op path and stay unaffected). ✅ Ran
   full suite, all green.
2. With both servers running, click "Refresh now" on the dashboard during
   market hours; confirm `fetch_current_quote` fires and a liquid stock's
   price matches its live quote elsewhere rather than lagging by a day.
3. Refresh again a few minutes later during market hours; price can move
   between refreshes (not just the freshness timestamp).
4. Refresh outside market hours (evening/weekend); behavior unchanged from
   before (last close shown, no spurious quote calls).

## Decisions

- Added the `currentPrice` clarifying note to `docs/api-contract.md` (value
  semantics only, no shape/version bump).
- Applied the live-quote overlay everywhere `fetch_daily_history` is called,
  including the screener batch and screener detail, not just the tracked
  watchlist.
