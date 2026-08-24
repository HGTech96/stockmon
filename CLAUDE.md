# stockmon

Personal stock buy/sell decision helper. Single local user. The app suggests
(POSSIBLE BUY / WAIT / POSSIBLE SELL) with full visible reasoning; the human
always decides. No automated trading, no AI features, no black-box scoring.

## Planning workflow
- Before implementing any phase, write the plan to docs/planning/phase-<N>-<name>.md
  and STOP for my review. Implement only after I approve.
- Plan format: clean markdown — short overview, then sections with headers:
  files to create/change (as a tree), schemas/interfaces (code blocks),
  step-by-step task list (checkboxes), open questions for me at the end.
  No walls of prose; scannable over exhaustive.
- After my review feedback, update the SAME file, don't create a new one.
- After implementation, mark completed steps in the plan file.

## Key documents (read when relevant, don't assume)

- docs/api-contract.md — the API contract. Endpoints and JSON shapes are FIXED.
  Never change a response shape without asking me first.
- docs/product-spec.md — original product brief and principles.
- docs/plan.md — phased build plan with checkboxes. Work phase by phase,
  check items off as completed.

## Stack

- Backend: Python 3.12+, FastAPI, PostgreSQL (bare metal, no Docker), yfinance.
- Frontend: React + Vite, Tailwind, shadcn/ui, Recharts, TanStack Query.
- Monorepo: api/ and ui/.

## Architecture rules (non-negotiable)

- Layered backend: api/src/core/ (pure domain logic) → services/ → api routes → db/.
  Dependencies point inward only. core/ imports NOTHING from outer layers,
  no FastAPI, no SQLAlchemy, no I/O, no DB calls.
- core/ uses stdlib dataclasses only. Pydantic is confined to the API edge
  (request/response models that convert to/from core dataclasses).
- Market data access behind an ABC interface (MarketDataProvider);
  YFinanceProvider is the first implementation.
- Positions are DERIVED from the trades table (event-sourced). Never store
  a mutable position row.
- Every business rule (checklists, warning thresholds, sorting, position math)
  exists in exactly ONE core function. The API and any future consumer
  (e.g. alert bot) call the same function.
- All logic lives in the backend. The React UI only renders API responses:
  no calculations, no sorting, no re-derived flags in the frontend.

## Conventions

- API sends raw numbers and ISO timestamps; UI does all formatting.
- Suggestion labels are machine enums (BUY/WAIT/SELL); UI renders display text.
- Plain, non-jargon language in all user-facing text.
- Type hints everywhere in Python. Tests with pytest for core/ logic
  (indicators, evaluation, position math are pure functions — test them).
- ui/ uses vitest for pure client-side logic (e.g. lib/tableViewState.js)
  — same "test the pure functions" principle as backend core/, applied to
  the one sanctioned place the UI computes anything (see the view-state
  exception below). Run with `npm test` in ui/.
- Small, focused commits per completed plan item.


## UI & Design

### Visual source of truth
- design/reference/ contains the exported design prototype (plain HTML/CSS/JS).
  Replicate its look in React: extract its exact colors, fonts, spacing, and
  radii into the Tailwind config once, and use theme tokens everywhere —
  never hardcode hex values in components. Never import or copy its code
  directly; it uses mock data and is reference-only.
- Badge colors are semantic and fixed: green = BUY/profit, orange = SELL/
  warning, gray = WAIT/neutral, red only for negative P/L numbers.
- A suggestion badge is never rendered without its checklist visible nearby.
- Every page shows the data-freshness timestamp from meta; stale data shows
  the stale warning.

### Code rules
- Language: plain JavaScript (no TypeScript). The API client layer carries
  JSDoc type comments matching docs/api-contract.md so autocomplete works.
- Structure: ui/src/api/ (client + JSDoc types), pages/ (one folder per page),
  components/ (shared: badges, cards, charts), lib/ (formatting helpers only).
- One component per file. A component over ~100 lines must be split.
- Pages compose components; components render props. Data fetching happens in
  page-level hooks (TanStack Query), never inside leaf components.
- All formatting (currency, %, dates, "N to go") lives in lib/format.js —
  never inline in JSX.
- No cleverness: no HOCs, no render props, no context unless unavoidable,
  no premature abstractions. Boring, flat, explicit code.
- The UI computes nothing: no sorting, no derived flags, no counting —
  render what the API sends.

## UI table view-state (sorting/filtering exception)
- The server owns the DEFAULT row order (attention-first) and remains the
  landing state. User-initiated column sorting and filtering are presentational
  view overrides applied client-side to already-fetched rows — no new API calls,
  no persistence, reset to server default on reload. This is the one sanctioned
  place the UI reorders/hides rows; the "UI computes nothing" rule still holds
  for all values, suggestions, and the default ordering.

## Screener (separate subsystem — Phase 14)

The screener is a distinct tool from the tracked watchlist/dashboard. Keep them
separate:

- Its universe is a plain text file (screener_stocks.txt), user-edited, ~150
  tickers, NOT stored in the stocks table and NOT related to the tracked
  watchlist.
- Results are precomputed by a manual terminal job (scripts/run_screener.py)
  into the screener_results table (latest run only, truncate+rewrite). The
  screener page reads that cache; it never triggers the batch fetch itself.
- The screener reuses the existing core evaluation/indicator functions — never
  reimplement analysis. Screener evaluation is entry-only (BUY/WAIT); there are
  no positions, cash, targets, or exit logic in the screener.
- Viewing a screener stock's detail (GET /api/screener/{ticker}/detail) is a
  LIVE fetch, computed and discarded — it does NOT persist into daily_prices or
  the watchlist.
- The only way a screener stock enters the tracked watchlist is the explicit
  "Track this stock" action, which routes through the normal Phase 11b
  add-stock flow. Casual viewing never modifies tracked data.
- Screener batch-fetch tuning (batch size, pause between batches) lives as named
  constants at the top of run_screener.py so it can be dialed if rate-limited.

## Don't

- Don't add features outside docs/plan.md without asking.
- Don't add auth, Docker, websockets, caching layers, or job queues.
- Don't put business logic in API routes or React components.
- Don't invent indicator formulas — RSI is standard 14-period Wilder RSI.
