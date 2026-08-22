# stockmon

Personal stock monitoring for small, deliberate buy/sell decisions.

## Contents

- [What It Does](#what-it-does)
- [Stack](#stack)
- [Repository Map](#repository-map)
- [How The App Thinks](#how-the-app-thinks)
- [Bare Metal Start](#bare-metal-start)
- [Everyday Development](#everyday-development)
- [Utility Scripts](#utility-scripts)
- [Environment Variables](#environment-variables)
- [Testing Notes](#testing-notes)
- [Product Boundaries](#product-boundaries)
- [Reference Docs](#reference-docs)
- [License](#license)

stockmon is a local-first decision helper for a small watchlist. It pulls recent
market data, computes transparent technical indicators, and turns them into a
plain-language suggestion:

- `POSSIBLE BUY`
- `WAIT`
- `POSSIBLE SELL`

The suggestion is never the whole story. Every recommendation is backed by the
conditions that produced it, the raw indicators, position context, freshness
metadata, and links to check market news manually before acting.

> stockmon does not trade, does not predict the market, and does not provide
> financial advice. It is built to slow decisions down and make the reasoning
> visible.

## What It Does

stockmon helps answer three practical questions:

| Question | Where it shows up | What drives it |
| --- | --- | --- |
| What should I look at first? | Dashboard | Backend-sorted watchlist with SELL, BUY, warnings, WAIT, and insufficient-history states |
| Why is this stock flagged? | Stock detail | Checklist conditions, RSI, trend, price position, volume, and sharp-move warnings |
| Am I close to my sell plan? | Portfolio | Average cost, current value, profit/loss, and per-position profit targets |

The product is intentionally simple:

- One local user
- Under 20 watchlist stocks
- Short-term view over the current day, 7 days, and 30 days
- Rule-based suggestions, no AI, no broker sync, no automated trading
- Visible reasoning over black-box scores

## Stack

| Layer | Technology |
| --- | --- |
| API | Python 3.12, FastAPI, SQLAlchemy, Alembic, yfinance |
| Database | PostgreSQL, managed directly on your machine |
| UI | React 19, Vite 8, Tailwind CSS 4, TanStack Query, Recharts, shadcn/base-ui pieces |
| Tests | pytest for backend logic and routes, oxlint for frontend linting |

## Repository Map

```text
stockmon/
  api/
    src/stockmon/
      api/          FastAPI routes and response schemas
      core/         Pure domain logic: indicators, suggestions, positions
      db/           SQLAlchemy models, sessions, persistence helpers
      services/     Application workflows over core + db + market data
      main.py       FastAPI app entrypoint
    alembic/        Database migrations
    scripts/        Local utility scripts, including watchlist seeding
    tests/          Backend test suite
  ui/
    src/
      api/          Fetch client and endpoint wrappers
      components/   Shared UI primitives and visual components
      pages/        Dashboard, stock detail, portfolio, history
      lib/          Formatting helpers
    vite.config.js  Vite dev proxy for /api -> localhost:8000
  docs/
    api-contract.md API shapes and backend/frontend contract
    product-spec.md Product principles and MVP scope
    planning/       Phase plans
  design/
    reference/      Static design reference assets
```

## How The App Thinks

The backend owns all business logic. The UI renders what the API says.

```text
yfinance
  -> refresh service
  -> PostgreSQL daily_prices
  -> core indicators and evaluation rules
  -> FastAPI JSON contract
  -> React views
```

Important rules:

- Watched stocks without a position use entry logic: BUY or WAIT.
- Held stocks use exit logic first: SELL can win only when the profit target is
  reached and at least one technical condition agrees.
- Sharp price moves trigger a warning to check news before acting.
- Positions are derived from the trade log. There is no mutable positions table.
- Freshness metadata is returned on GET responses and shown in the UI.

## Bare Metal Start

This is the direct local setup. No Docker, no containers, no hidden services.

### 1. Install System Prerequisites

You need:

- Python `3.12+`
- Poetry
- PostgreSQL running locally
- Node.js `20.19+` or `22.12+`
- npm

On macOS with Homebrew, the shape is typically:

```bash
brew install python@3.12 poetry postgresql node
brew services start postgresql
```

If your PostgreSQL package is versioned, start that service instead, for example
`postgresql@16` or `postgresql@17`.

### 2. Create Local Databases

Create a local PostgreSQL user and databases:

```bash
psql postgres
```

```sql
CREATE USER stockuser WITH PASSWORD 'stockpass';
CREATE DATABASE stockmon OWNER stockuser;
CREATE DATABASE stockmon_test OWNER stockuser;
\q
```

If you already have a PostgreSQL user, reuse it and adjust `api/.env`.

### 3. Configure The API

```bash
cd api
cp .env.example .env
```

Edit `api/.env` so the database URLs match your local credentials:

```env
DATABASE_URL=postgresql+psycopg://stockuser:stockpass@localhost:5432/stockmon
TEST_DATABASE_URL=postgresql+psycopg://stockuser:stockpass@localhost:5432/stockmon_test
UI_ORIGIN=http://localhost:5173
```

### 4. Install Backend Dependencies

```bash
cd api
poetry install
```

### 5. Migrate And Seed

```bash
cd api
poetry run alembic upgrade head
poetry run python scripts/seed_watchlist.py
```

The seed script is idempotent. Running it again will skip stocks that already
exist.

### 6. Start The API

Terminal 1:

```bash
cd api
poetry run stockmon
```

The API listens on:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

### 7. Install And Start The UI

Terminal 2:

```bash
cd ui
npm install
npm run dev
```

The UI runs on:

```text
http://localhost:5173
```

Vite proxies `/api` requests to `http://localhost:8000`, so keep both processes
running during development.

### 8. Pull Market Data

With the API running, trigger a refresh:

```bash
curl -X POST http://localhost:8000/api/refresh
```

This downloads recent watchlist data through `yfinance`, writes daily prices to
PostgreSQL, and returns a list of refreshed and failed tickers. Partial failures
are allowed; the app will show stale metadata where needed.

## Everyday Development

### Backend

```bash
cd api
poetry run pytest
poetry run alembic upgrade head
poetry run stockmon
```

Useful API URLs:

```text
GET  http://localhost:8000/api/health
GET  http://localhost:8000/api/stocks
GET  http://localhost:8000/api/stocks/AAPL
GET  http://localhost:8000/api/portfolio
GET  http://localhost:8000/api/trades
GET  http://localhost:8000/api/settings
POST http://localhost:8000/api/refresh
POST http://localhost:8000/api/trades
PUT  http://localhost:8000/api/settings
PUT  http://localhost:8000/api/settings/targets/{ticker}
```

### Frontend

```bash
cd ui
npm run dev
npm run build
npm run lint
```

The frontend keeps calculations out of React components. Sorting, suggestion
logic, checklist counts, warning decisions, and position math come from the API.

## Utility Scripts

All scripts live in `api/scripts/` and are invoked directly (no `argparse`,
no console-script entries) with `poetry run python scripts/<name>.py` from
the `api/` directory. They talk to `DATABASE_URL` from `api/.env`, same as
the running API.

### `seed_watchlist.py`

Inserts the hardcoded watchlist tickers into the `stocks` table. Idempotent —
already-present tickers are skipped and reported separately from newly added
ones.

```bash
cd api
poetry run python scripts/seed_watchlist.py
```

### `reset_to_initial_state.py`

Wipes all `trades` and `cash_events` rows, clearing every position, the trade
history, and the cash balance. Stocks and price history are left untouched.
Positions and portfolio are derived from the trades table, so deleting trades
is sufficient — there's no separate positions table to reset.

```bash
cd api
poetry run python scripts/reset_to_initial_state.py
```

### `import_history.py`

Bulk-loads a chronologically ordered CSV of past deposits, withdrawals,
buys, and sells into an already-populated database (a top-up, not a fresh
seed). Every row is replayed through the same sequence-validation the live
API uses (share-oversell, cash-oversell, same-day money-in-before-out), and
duplicate rows — exact matches on all six fields, against either the
existing database or an earlier row in the same file — are rejected. The
import is all-or-nothing: any failure aborts the whole file before anything
is written, and the error names the offending line number.

```bash
cd api
poetry run python scripts/import_history.py path/to/history.csv
```

CSV columns: `date,type,ticker,shares,price,amount`, with `date` in ISO
`YYYY-MM-DD` and `type` one of `deposit`, `withdraw`, `buy`, `sell`.
`shares`/`price` apply to `buy`/`sell`; `amount` applies to
`deposit`/`withdraw`; leave the rest blank. See
[the phase plan](docs/planning/phase-10b-csv-importer.md) for the full
design.

## Environment Variables

| Variable | Required | Used by | Purpose |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | API, Alembic | Main PostgreSQL database |
| `TEST_DATABASE_URL` | Yes for tests | pytest | Isolated test database |
| `UI_ORIGIN` | No | API CORS | Allowed browser origin, defaults to `http://localhost:5173` |

The API resolves `.env` from `api/.env`, so commands work from `api/`, the repo
root, or an IDE run configuration after dependencies are installed.

## Testing Notes

The backend tests expect `TEST_DATABASE_URL` to point at an existing PostgreSQL
database. Create it once, then run:

```bash
cd api
poetry run pytest
```

The UI can be checked with:

```bash
cd ui
npm run lint
npm run build
```

## Product Boundaries

In scope:

- Watchlist dashboard
- Stock detail indicators and explanations
- Portfolio and trade-log based position math
- Profit target tracking
- Data freshness and stale-data warnings
- Manual news links

Out of scope for the MVP:

- Automated trading
- Broker sync
- AI recommendations or news analysis
- Alerts and background jobs
- Authentication
- Backtesting
- Tax reporting

## Reference Docs

- [Product spec](docs/product-spec.md)
- [API contract](docs/api-contract.md)
- [Implementation plan](docs/plan.md)
- [Planning notes](docs/planning/)

## License

No license file is currently included.
