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
### 9c Design review — after 9b
### 9d Finalization (wire approved design to real endpoints) — after 9c