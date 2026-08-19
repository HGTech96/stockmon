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
- [ ] GET /api/stocks (dashboard, server-side sorting per contract)
- [ ] GET /api/stocks/{ticker} (detail incl. insufficient-history state)
- [ ] GET /api/portfolio (incl. empty state)
- [ ] POST /api/trades (validation per contract, returns updated position)
- [ ] GET/PUT settings endpoints (profit targets)
- [ ] Endpoint tests against contract examples

## Phase 4 — UI skeleton
- [ ] ui/ scaffold: Vite + React + Tailwind + shadcn/ui + TanStack Query + router
- [ ] API client layer typed to the contract shapes
- [ ] Layout shell: nav, data-freshness bar (timestamp, stale warning)

## Phase 5 — Pages
- [ ] Dashboard page (table, badges, warning icons, summary strip)
- [ ] Stock detail page (badge + checklist, charts with overlays, indicators table, position card, news links, warning banner, insufficient-data state)
- [ ] Portfolio page (positions, totals, target progress, empty state)
- [ ] Add/Edit trade modal (validation, shows server-returned updated position)

## Phase 6 — Polish
- [ ] Auto-refetch interval via TanStack Query
- [ ] Loading and error states on all pages
- [ ] Settings page for profit targets
- [ ] End-to-end pass: fresh DB → seed → refresh → record trades → verify all pages