# stockmon

Personal stock buy/sell decision helper. Single local user. The app suggests
(POSSIBLE BUY / WAIT / POSSIBLE SELL) with full visible reasoning; the human
always decides. No automated trading, no AI features, no black-box scoring.

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
- Small, focused commits per completed plan item.

## Don't

- Don't add features outside docs/plan.md without asking.
- Don't add auth, Docker, websockets, caching layers, or job queues.
- Don't put business logic in API routes or React components.
- Don't invent indicator formulas — RSI is standard 14-period Wilder RSI.