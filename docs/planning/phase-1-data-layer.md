# Phase 1 — Data Layer

## Context

Phase 0 built the FastAPI skeleton, SQLAlchemy models (`stocks`, `daily_prices`,
`trades`, `settings`, `profit_targets`), the initial Alembic migration, and a
seed script with the 13-ticker watchlist. `core/`, `services/`,
`api/routes/`, `api/schemas/` are empty stub packages — no code to preserve,
but the package layout is fixed.

Phase 1 makes the app able to pull real price history from Yahoo Finance and
store it, via `POST /api/refresh` per the fixed API contract. This is the
foundation Phase 2 (indicators/evaluation) reads from.

Verified directly from `api/src/stockmon/db/models.py`:
- `DailyPrice` has a unique constraint `uq_daily_price_stock_date` on
  `(stock_id, trade_date)` — the upsert key.
- Columns: `trade_date: Date`, `open/high/low/close: Numeric(12,4)`,
  `volume: BigInteger`.
- `Stock` has no `is_watchlist` flag — every row in `stocks` **is** the
  watchlist.
- Stack confirmed from `pyproject.toml`: sync SQLAlchemy 2.0, `psycopg[binary]
  ^3.2` (not psycopg2/asyncpg), `yfinance ^0.2` already a dependency.
- DB session pattern: `db/session.py::get_db()` (sync generator, standard
  FastAPI `Depends`).
- `main.py` currently defines `/api/health` inline on `app`; no router
  registered yet.

## Decisions from review

- `fetch_current_quote` **is** included in the `MarketDataProvider` ABC and
  implemented in `YFinanceProvider` (per docs/plan.md's wording), but it is
  **not called** anywhere in Phase 1 — `currentPrice` for later phases will
  read the latest `daily_prices` row. It sits ready for whenever something
  actually needs a live quote.
- Staleness tracking (`meta.dataAsOf` / `isStale` for GET endpoints) is
  **deferred to Phase 3**. Phase 1's refresh response only reports the time
  the refresh call itself finished — no new column, no migration this phase.

## Files to create/change

```
api/src/stockmon/
├── core/
│   └── market_data.py          NEW — DailyBar, Quote (dataclasses),
│                                      MarketDataError, MarketDataProvider (ABC)
├── services/
│   ├── yfinance_provider.py    NEW — YFinanceProvider(MarketDataProvider)
│   └── refresh_service.py      NEW — RefreshFailure, RefreshResult, refresh_all_stocks()
├── db/
│   └── daily_prices.py         NEW — upsert_daily_prices() (Postgres ON CONFLICT)
├── api/
│   ├── schemas/
│   │   ├── base.py             NEW — CamelModel (shared camelCase base for all future schemas)
│   │   └── refresh.py          NEW — RefreshFailureItem, RefreshResponse
│   └── routes/
│       └── refresh.py          NEW — get_market_data_provider dep + POST /api/refresh
└── main.py                     EDIT — include_router(refresh.router)

api/tests/
└── services/
    ├── __init__.py             NEW (empty)
    └── test_refresh_service.py NEW — partial-failure aggregation, fake provider + mocked upsert
```

## Schemas / interfaces

**`core/market_data.py`** — pure, no yfinance/SQLAlchemy/FastAPI imports:

```python
@dataclass(frozen=True)
class DailyBar:
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

@dataclass(frozen=True)
class Quote:
    price: Decimal
    as_of: datetime

class MarketDataError(Exception):
    """Raised by any MarketDataProvider on a per-ticker fetch failure."""

class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]: ...
    @abstractmethod
    def fetch_current_quote(self, ticker: str) -> Quote: ...
```

**`services/yfinance_provider.py`**:

```python
class YFinanceProvider(MarketDataProvider):
    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        # yf.Ticker(ticker).history(start=today-days, end=today+1)
        # wraps any exception / empty result in MarketDataError

    def fetch_current_quote(self, ticker: str) -> Quote:
        # yf.Ticker(ticker).fast_info["last_price"]; wraps failures in MarketDataError
```

**`db/daily_prices.py`**:

```python
def upsert_daily_prices(db: Session, stock_id: int, bars: list[DailyBar]) -> int:
    """INSERT ... ON CONFLICT (stock_id, trade_date) DO UPDATE, via uq_daily_price_stock_date.
    Idempotent: rerunning with the same bars is a no-op update. Returns rows upserted."""
```

**`services/refresh_service.py`**:

```python
DEFAULT_HISTORY_DAYS = 60

@dataclass(frozen=True)
class RefreshFailure:
    ticker: str
    error: str

@dataclass(frozen=True)
class RefreshResult:
    refreshed: list[str]
    failed: list[RefreshFailure]
    data_as_of: datetime

def refresh_all_stocks(
    db: Session, provider: MarketDataProvider, days: int = DEFAULT_HISTORY_DAYS
) -> RefreshResult:
    """Loops every Stock row. Per ticker: fetch -> upsert -> commit.
    On MarketDataError: rollback that ticker's partial work, record failure, continue.
    One ticker's failure never aborts the others (per-ticker atomic, not per-row)."""
```

**`api/schemas/base.py`**:

```python
class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
```

**`api/schemas/refresh.py`** (matches `docs/api-contract.md` §5 exactly):

```python
class RefreshFailureItem(CamelModel):
    ticker: str
    error: str

class RefreshResponse(CamelModel):
    refreshed: list[str]
    failed: list[RefreshFailureItem]
    data_as_of: datetime   # serializes as "dataAsOf", ISO-8601 with offset
```

**`api/routes/refresh.py`**:

```python
def get_market_data_provider() -> MarketDataProvider:
    return YFinanceProvider()

router = APIRouter()

@router.post("/api/refresh", response_model=RefreshResponse)
def refresh(
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> RefreshResponse:
    result = refresh_all_stocks(db, provider)
    return RefreshResponse(
        refreshed=result.refreshed,
        failed=[RefreshFailureItem(ticker=f.ticker, error=f.error) for f in result.failed],
        data_as_of=result.data_as_of,
    )
```

## Task list

- [x] `core/market_data.py`: `DailyBar`, `Quote`, `MarketDataError`, `MarketDataProvider`
- [x] `services/yfinance_provider.py`: `YFinanceProvider` implementing both ABC methods
- [x] `db/daily_prices.py`: `upsert_daily_prices()` using `postgresql.insert(...).on_conflict_do_update(...)`
- [x] `services/refresh_service.py`: `RefreshFailure`, `RefreshResult`, `refresh_all_stocks()`
- [x] `api/schemas/base.py`: `CamelModel`
- [x] `api/schemas/refresh.py`: `RefreshFailureItem`, `RefreshResponse`
- [x] `api/routes/refresh.py`: DI provider + `POST /api/refresh`
- [x] `main.py`: register the refresh router
- [x] `tests/services/test_refresh_service.py`: partial-failure aggregation, using a fake
      `MarketDataProvider` and a mocked `upsert_daily_prices` (no real DB/network needed)
- [x] Manual verification: ran the dev server (port 8010, since 8000 was occupied by an
      existing PyCharm-launched instance), `POST /api/refresh` against the real 13-ticker
      watchlist — all 13 refreshed, 0 failures, 41 rows each / 533 total in `daily_prices`
      (2026-06-22 .. 2026-08-18). Re-ran refresh: row count stayed at 533, confirming the
      upsert is idempotent.
- [x] Check off Phase 1 items in `docs/plan.md`

## Open questions

1. **Upsert granularity** — per-ticker atomic (rollback that ticker's partial batch on
   failure, other tickers unaffected) is the assumed model. Confirm that matches intent.
2. **`DEFAULT_HISTORY_DAYS = 60`** — hardcoded constant in `refresh_service.py` for
   now, not exposed via `Settings`/env var. OK for MVP, or should it be configurable now?
3. yfinance can hit rate-limiting/anti-bot responses intermittently (no retry logic
   planned this phase — a failure just lands in `failed[]` with `error` text). If the
   real watchlist refresh shows this is a real problem, we'll address it as a fast
   follow rather than in this plan.

---

**Status: approved via plan-mode review on 2026-08-19. Proceeding to implementation.**
