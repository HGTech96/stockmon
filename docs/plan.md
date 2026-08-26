# stockmon — Build Plan

Work one phase at a time. Check off items as they're completed and verified.
Do not start a phase before the previous one is done and committed.

## Phase 0 — Skeleton
- [x] api/ project scaffold: FastAPI app, folder layout (core/, services/, api/, db/), pyproject.toml, pytest setup
- [x] Postgres database + SQLAlchemy models: stocks, daily_prices, trades, settings
- [x] Alembic migration for initial schema
- [x] Seed script: insert my watchlist tickers
- [x] Health endpoint, app runs locally

## Phase 1 — Data layer
- [x] MarketDataProvider ABC in core (interface: fetch daily history, fetch current quote)
- [x] YFinanceProvider implementation
- [x] Refresh service: download ~60 days per ticker, upsert into daily_prices
- [x] POST /api/refresh per contract (partial-failure handling, stale tracking)
- [x] Manual test: refresh real watchlist, verify rows in DB

## Phase 2 — Core logic (pure functions + tests)
- [x] Indicator calculations: changes, 30d avg/high/low, distances, volume vs avg, 14-period Wilder RSI
- [x] Entry evaluation (4 conditions, ≥3 → BUY) returning structured checklist
- [x] Exit evaluation (target + technicals) returning structured checklist
- [x] Precedence rule for owned stocks (exit SELL > entry BUY > WAIT)
- [x] Sharp-move warning rule (>5% 1d or >10% 7d)
- [x] Position derivation from trades (weighted avg cost, sells, closing at zero)
- [x] Unit tests for ALL of the above, including edge cases (insufficient history, zero volume)

## Phase 3 — API endpoints
- [x] GET /api/stocks (dashboard, server-side sorting per contract)
- [x] GET /api/stocks/{ticker} (detail incl. insufficient-history state)
- [x] GET /api/portfolio (incl. empty state)
- [x] POST /api/trades (validation per contract, returns updated position)
- [x] GET/PUT settings endpoints (profit targets)
- [x] Endpoint tests against contract examples

## Phase 4 — UI skeleton
- [x] ui/ scaffold: Vite + React + Tailwind + shadcn/ui + TanStack Query + router
- [x] API client layer typed to the contract shapes
- [x] Layout shell: nav, data-freshness bar (timestamp, stale warning)

## Phase 5 — Pages
- [x] Dashboard page (table, badges, warning icons, summary strip)
- [x] Stock detail page (badge + checklist, charts with overlays, indicators table, position card, news links, warning banner, insufficient-data state)
- [x] Portfolio page (positions, totals, target progress, empty state)
- [x] Add/Edit trade modal (validation, shows server-returned updated position)

## Phase 6 — Polish
- [ ] Auto-refetch interval via TanStack Query
- [ ] Loading and error states on all pages
- [ ] Settings page for profit targets
- [ ] End-to-end pass: fresh DB → seed → refresh → record trades → verify all pages

## Phase 7 — Trade history
- [x] Contract: GET /api/trades (see api-contract.md v1.2)
- [x] Core: realized P/L per sell trade (pure function + tests)
- [x] Backend: repository query, route, schema
- [x] UI: History page + nav tab, table per design system

## Phase 8 — Edit / delete trades
- [x] Contract: PUT and DELETE /api/trades/{id} (see api-contract.md v1.4)
- [x] Core: full trade-sequence validation (replay in date order; reject if
      any sell exceeds shares held at that point) — pure function + tests
      (reuses existing `derive_position` rather than a new function — see
      docs/planning/phase-8-edit-trades.md)
- [x] Backend: PUT (shares/price/date only), DELETE, both re-validating the
      whole sequence for the affected ticker
- [x] UI: edit + delete actions on trade history rows; edit modal (shares,
      price, date only — ticker read-only); confirm dialogs stating the
      downstream effect; invalidate stocks/portfolio/trades queries


## Phase 9 — Cash model + P/L breakdown
### 9a Backend
- [x] Contract v1.5 (cash model, /api/cash, money block)
- [x] cash_events table + migration
- [x] Core: cash balance derivation (replay deposits/withdrawals/buys/sells)
- [x] Core: sequence validation extended — buys/withdrawals can't oversell cash
- [x] Core: the six money figures (pure functions + tests, incl. the identity)
- [x] GET/POST /api/cash, DELETE /api/cash/{id}
- [x] money block on dashboard + portfolio summaries
- [x] Buy rejected (422) on insufficient cash
### 9b Design (static mockup, dummy numbers) — after 9a
- [x] MoneyTile/MoneyCluster/MoneyStrip components + /preview/cash route
      (see docs/planning/phase-9b-design.md)
### 9c Design review — after 9b
- [x] Layout/placement feedback applied (cluster bottom-edge alignment,
      full-cell live tint, +/− icon buttons) and live-tint treatment
      decided (dot + caption + tint) — see phase-9b-design.md
### 9d Finalization (wire approved design to real endpoints) — after 9c
- [x] MoneyStrip wired to the live `money` block on dashboard + portfolio;
      EmptyMoneyStrip bootstrap state when `money` is null (fresh DB);
      Deposit/Withdraw via `CashModal` (POST /api/cash), inline 422s;
      insufficient-cash buy 422 verified through TradeModal's existing
      error display; `/preview/cash` removed
      (see docs/planning/phase-9d-finalize.md)

## Phase 10 — Data handling improvements
### 10a Fractional shares
- [x] Migration: trades.shares → Numeric(12,6)
- [x] Core: Decimal for shares everywhere (position, realized P/L, cash reconcile
      — already Decimal end to end; sweep found no int assumption in core/)
- [x] API: accept fractional shares, still reject <= 0
- [x] UI: shares input accepts decimals; lib/format.js trims trailing zeros
- [x] Tests: fractional buy draws exact cash; partial fractional sell
- [x] Contract version bump (v1.6, see docs/planning/phase-10a-fractional-shares.md)
### 10b CSV history importer
- [x] scripts/import_history.py — one ordered CSV (date,type,ticker,shares,price,amount)
- [x] Replays every row through existing core sequence-validation (reuse, don't bypass)
- [x] Runs against an already-populated DB (top-up)
- [x] Duplicate = exact match on all six fields vs DB (and within the same CSV) → abort whole import, named row
- [x] Atomic: any validation failure OR duplicate → nothing written, error names the row
- [x] Fractional shares supported (10a first)
### 10c Dashboard refresh button
- [x] "Refresh now" button directly above the dashboard stock table
- [x] Calls existing POST /api/refresh; invalidates stocks/portfolio/cash queries
- [x] In-flight disabled/loading state (refresh takes seconds)
- [x] Surface `failed` tickers from the response as an inline notice
- [x] If a refresh button already exists (Phase 6 shell), MOVE it here, don't duplicate
      (none existed — Phase 6's auto-refetch interval had no user-facing
      button; this is net-new, see docs/planning/phase-10c-refresh-button.md)

## Phase 11 — Adjustments
### 11a Money widgets: Portfolio only
- [ ] Remove the MoneyStrip from the Dashboard page (keep on Portfolio)
- [ ] API unchanged (money block still returned; dashboard just doesn't render it)
### 11b Add stock to watchlist
- [x] Backend: POST /api/stocks — validate ticker via provider, fetch history, store
- [x] Contract: new endpoint (v1.7); 422 unknown ticker, 409 already on watchlist
- [x] UI: "Add" button beside "Refresh now" above the dashboard table; modal with
      ticker input, inline 422 on unknown ticker; invalidate stocks query on success
      (see docs/planning/phase-11b-add-stock.md)

## Phase 12 — Table sorting
- [x] Shared table view-state layer (extensible for Phase 13 filtering)
- [x] Every column sortable on Dashboard and Portfolio
- [x] Three-state header cycle: asc → desc → server default
- [x] Nulls always last, regardless of direction
- [x] No persistence; reload resets to server default
      (see docs/planning/phase-12-sorting.md)

## Phase 13 — Table filtering
- [x] Plugs into the Phase 12 shared view-state layer (sort + filter combine)
- [x] Text search (both tables): ticker or company name, case-insensitive substring
- [x] Suggestion filter (both tables): BUY / WAIT / SELL toggles, multi-select
- [x] Owned/not-owned filter (dashboard only)
- [x] Client-side only, no persistence, reset-all affordance
- [x] Empty-result state distinct from other empty states
      (see docs/planning/phase-13-filtering.md)

## Phase 14 — Stock screener (separate tool from the main dashboard)

A screener that evaluates a large, separate universe (~150 stocks) read from a
plain text file, precomputed by a manually-run terminal job, results cached in
a table and shown on a separate page. NOT the tracked watchlist — shares no data
with the stocks/daily_prices tables. Reuses all existing core evaluation.

### 14a Backend: screener job + results
- [x] screener_stocks.txt (one ticker per line; user-edited, not in DB; ship an example)
- [x] screener_results table (latest run only): ticker, company_name,
      current_price, change_1d_pct, suggestion, conditions_met, conditions_total,
      rsi, price_vs_30d_avg_pct, sharp_move, run_at
- [x] scripts/run_screener.py: read file; batched fetch (size ~10, 1–2s pause
      between batches, both tunable constants); evaluate via existing core
      (entry-only BUY/WAIT); truncate+rewrite results atomically; concise
      terminal logging; failed ticker skipped not fatal
- [x] GET /api/screener: latest-run rows + run_at; explicit never-run state
- [x] Contract amendment (v-bump) for GET /api/screener
      (see docs/planning/phase-14a-screener-backend.md)

### 14b Backend: live-fetch detail endpoint
- [x] GET /api/screener/{ticker}/detail: live-fetch one ticker's history (not
      stored), compute full indicators + entry evaluation via existing core,
      return the same payload shape as an UNOWNED stock's detail (no position
      card, entry-only suggestion, chart + indicators + news)
- [x] 422/handled state if the ticker can't be fetched
- [x] Contract amendment (v-bump)

### 14c Frontend: screener page + click-through + promote
- [x] Separate /screener route (not the main dashboard)
- [x] Dashboard-style table reusing the Phase 12/13 sort+filter view-state layer
- [x] Columns: ticker+name, price, 1d change, suggestion, conditions-met, RSI,
      price-vs-30d-avg, sharp-move indicator
- [x] "Last run" timestamp; never-run empty state ("Run the screener job first")
- [x] Row click → detail page (unowned form) fed by the 14b live-fetch endpoint
- [x] "Track this stock" action on that detail → promotes to watchlist via the
      existing Phase 11b add-stock flow
      (see docs/planning/phase-14c-screener-page.md)

## Phase 15 — Screener refresh button

Adds an on-demand "Refresh" button on the screener page that runs the full
batch job (previously terminal-only) via a new synchronous endpoint. Shared
batch-fetch logic between the terminal script and the endpoint; no job queue.

- [x] run_screener_batch() shared service function (screener_service.py),
      used by both scripts/run_screener.py and the new endpoint
- [x] POST /api/screener/refresh: runs the batch, truncate+rewrites
      screener_results, returns refreshed/failed/runAt (v1.10 contract bump)
- [x] Screener page "Refresh" button (also shown as "Run screener" in the
      never-run empty state, replacing the old terminal-only instruction)
      (see docs/planning/phase-15-screener-refresh.md)