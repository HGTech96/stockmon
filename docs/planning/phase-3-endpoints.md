# Phase 3 — API Endpoints

## Context

Phases 0–2 built the skeleton, the refresh pipeline (`services/refresh_service.py`,
`routes/refresh.py` — done, contract-compliant, untouched by this phase), and
pure `core/` logic (`indicators.py`, `position.py`, `evaluation.py`) with unit
tests. Phase 3 wires all of that to the remaining five contract endpoints
(dashboard, stock detail, portfolio, trades, settings), matching
`docs/api-contract.md` v1.1 exactly, including the `meta` freshness block,
server-side dashboard sorting, all special states (empty portfolio,
insufficient history, stale data), and trade validation.

Verified gaps that this phase must close:
- **No staleness tracking exists.** `refresh_all_stocks` computes
  `data_as_of = datetime.now()` inline and persists nothing. Every GET's
  `meta` block needs a real, minimal mechanism — see Design decisions.
- **`Settings` is never seeded.** The model has a Python-level
  `default=Decimal("50.00")` but no row is ever inserted. `settings_service`
  must get-or-create the `id=1` row.
- **Pydantic v2 serializes `Decimal` as a JSON string** (`"6.90"`), which
  violates the contract's "raw numbers" rule. Fix: a `Money` type alias
  (`Annotated[Decimal, PlainSerializer(float, ...)]`) used on every
  currency/percentage/shares response field, so JSON output is a bare
  number while internal math stays `Decimal`.
- **`googleFinance` needs an exchange suffix** (e.g. `AAPL:NASDAQ`) but
  `stocks` has no `exchange` column, and the seeded watchlist (`api/scripts/seed_watchlist.py`)
  is not all-NASDAQ (`ORCL` is NYSE). Dropping the suffix and linking to
  the ticker-only URL is the proposed fix — see open questions.
- Two small pure additions are needed in `core/` that don't exist yet: a
  profit-target-progress calculation (reused by stock detail *and*
  portfolio) and a price-only fallback for stocks with `<30` days of
  history (dashboard/detail must still show `currentPrice`/`change1dPct`
  even in `insufficient_history` status).

## Design decisions

1. **Staleness** — new singleton table `refresh_status` (id=1):
   `last_attempted_at`, `last_succeeded_at` (nullable), `had_failures`.
   `routes/refresh.py` calls `freshness_service.record_refresh_result()`
   after `refresh_all_stocks()`. Every GET route calls
   `freshness_service.get_freshness(db)`. The actual `dataAsOf`/`isStale`
   logic is a **pure** `core/freshness.py` function taking `now` as a
   parameter (testable without mocking the clock). This is global, not
   per-ticker: a partial refresh failure marks the whole response stale
   even for tickers that did refresh successfully — simplest correct
   behavior for a single-user tool with <20 tickers.
2. **Dashboard sort lives in `core/`** — CLAUDE.md explicitly lists sorting
   as a business rule that must exist in exactly one function.
   `core/dashboard.py::sort_dashboard_rows()` takes duck-typed rows and
   orders them: `SELL(0) → BUY(1) → warning-only(2) → WAIT(3) →
   insufficient_history(4)`, ticker-alphabetical tiebreak within a bucket.
   "Warning-only" = has a warning but suggestion isn't SELL/BUY, so a
   WAIT-with-warning sorts ahead of a plain WAIT.
3. **`metCount`/`totalCount`** computed at the schema layer
   (`len(checklist)` / count of `passed`), not added to the core
   `Suggestion` dataclass — it's a pure derived count, not a new rule, so
   core stays untouched.
4. **Decimal → JSON**: `Money = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]`
   in `schemas/base.py`, used on every response field. Request bodies keep
   plain `Decimal` (Pydantic parses JSON numbers into `Decimal` safely via
   string conversion, no binary-float artifacts).
5. **Error shape normalization** — two exception handlers in `main.py`
   (not per-route try/except): `RequestValidationError` (Pydantic body
   errors) and a new `TradeValidationError` (domain rule violations) both
   map to `422 {"error": "<message>"}`. A new `StockNotFoundError` maps to
   `404 {"error": "<message>"}` — reusing the same flat shape for
   consistency rather than FastAPI's default `{"detail": ...}`.
6. **Trade position math is always `derive_position` over the full
   replayed history** — never hand-adjusted. `trade_service.record_trade()`:
   load existing trades for the ticker sorted `(trade_date, id)` → derive
   `position_before` (for the two distinct sell-validation messages) →
   insert the new `Trade`, flush for its `id` → re-sort full event list
   incl. the new trade → `derive_position()` again for `position_after`,
   the literal source of `updatedPosition` → commit.
7. **Test infra**: real Postgres, separate `stockmon_test` database (not
   sqlite — `daily_prices.py` uses `postgresql.insert(...).on_conflict_do_update`,
   which sqlite doesn't support). Isolation via **truncate-before-each-test**
   rather than per-test SAVEPOINT rollback, because services call
   `db.commit()` directly (see `refresh_service.py`), which breaks
   transaction-rollback isolation. Tables created once per session via
   `Base.metadata.create_all`.

## Files to create/change

```
api/src/stockmon/core/
├── position.py            CHANGE — add ProfitTargetProgress, evaluate_profit_target()
├── indicators.py          CHANGE — add PriceSnapshot, calculate_price_snapshot()
├── dashboard.py           NEW — SortableStockRow protocol, sort_dashboard_rows()
└── freshness.py           NEW — Freshness, build_freshness()

api/src/stockmon/db/
├── models.py               CHANGE — add RefreshStatus model
└── refresh_status.py       NEW — get_or_create(db), record(db, ...)

api/alembic/versions/
└── <rev>_add_refresh_status.py   NEW migration (down_revision = dd8a7a949707)

api/src/stockmon/services/
├── freshness_service.py    NEW — get_freshness(db, now=None), record_refresh_result(db, result)
├── stock_service.py        NEW — evaluate_stock_snapshot(), shared by dashboard/detail/portfolio
├── dashboard_service.py    NEW — build_dashboard(db)
├── stock_detail_service.py NEW — get_stock_detail(db, ticker), StockNotFoundError
├── portfolio_service.py    NEW — get_portfolio(db)
├── trade_service.py        NEW — record_trade(db, ...), TradeValidationError
└── settings_service.py     NEW — get/update settings, get_effective_target()

api/src/stockmon/api/schemas/
├── base.py                 CHANGE — add Money type alias
├── common.py                NEW — MetaSchema, SuggestionSchema, WarningSchema, ProfitTargetSchema
├── dashboard.py              NEW
├── stock_detail.py           NEW
├── portfolio.py               NEW
├── trade.py                    NEW
└── settings.py                  NEW

api/src/stockmon/api/routes/
├── stocks.py                NEW — GET /api/stocks, GET /api/stocks/{ticker}
├── portfolio.py               NEW — GET /api/portfolio
├── trades.py                    NEW — POST /api/trades
├── settings.py                    NEW — GET/PUT /api/settings, PUT /api/settings/targets/{ticker}
└── refresh.py                       CHANGE — call freshness_service.record_refresh_result()

api/src/stockmon/main.py    CHANGE — include new routers, register exception handlers

api/tests/
├── conftest.py               NEW — test_engine/db/client fixtures + row-builder helpers
├── core/
│   ├── test_dashboard.py     NEW
│   ├── test_freshness.py     NEW
│   ├── test_position.py      CHANGE — add evaluate_profit_target cases
│   └── test_indicators.py    CHANGE — add calculate_price_snapshot cases
├── services/
│   ├── test_stock_service.py       NEW
│   ├── test_dashboard_service.py   NEW
│   ├── test_trade_service.py       NEW
│   └── test_settings_service.py    NEW
└── routes/
    ├── test_stocks_route.py        NEW — dashboard + detail, matches contract JSON
    ├── test_portfolio_route.py     NEW
    ├── test_trades_route.py        NEW
    └── test_settings_route.py      NEW
```

## Schemas / interfaces

**`core/position.py` addition**
```python
@dataclass(frozen=True)
class ProfitTargetProgress:
    target_dollars: Decimal
    progress_dollars: Decimal   # profit_loss clamped to [0, target_dollars]
    remaining_dollars: Decimal  # max(target_dollars - profit_loss, 0), uncapped above
    reached: bool                # profit_loss >= target_dollars (same test as evaluate_exit)

def evaluate_profit_target(profit_loss: Decimal, target_dollars: Decimal) -> ProfitTargetProgress: ...
```

**`core/indicators.py` addition**
```python
@dataclass(frozen=True)
class PriceSnapshot:
    current_price: Decimal
    change_1d_pct: Decimal

def calculate_price_snapshot(bars: list[DailyBar]) -> PriceSnapshot | None:
    """bars oldest-first. None if bars is empty (never-refreshed ticker).
    change_1d_pct = 0 if only 1 bar available."""
```

**`core/dashboard.py`**
```python
class SortableStockRow(Protocol):
    ticker: str
    status: Literal["ok", "insufficient_history"]
    suggestion_label: Literal["BUY", "WAIT", "SELL"] | None
    has_warning: bool

def sort_dashboard_rows(rows: list[T]) -> list[T]:
    """Bucket: SELL(0) < BUY(1) < warning-only(2) < WAIT(3) < insufficient_history(4).
    Ticker alphabetical tiebreak within a bucket."""
```

**`core/freshness.py`**
```python
@dataclass(frozen=True)
class Freshness:
    data_as_of: datetime
    is_stale: bool
    stale_message: str | None

def build_freshness(
    now: datetime,
    last_attempted_at: datetime | None,
    last_succeeded_at: datetime | None,
    had_failures: bool,
) -> Freshness:
    """
    - never refreshed (both None) -> data_as_of=now, is_stale=True,
      "No data yet — run a refresh to load prices."
    - had_failures -> data_as_of = last_succeeded_at or now, is_stale=True,
      "Couldn't refresh — showing the last known prices from {weekday}, {h:mm AM/PM}."
      (generic message, no timestamp clause, if never succeeded)
    - else -> data_as_of=last_succeeded_at, is_stale=False, stale_message=None
    """

def format_weekday_time(dt: datetime) -> str: ...  # "Monday, 4:00 PM"
```

**`db/models.py` addition**
```python
class RefreshStatus(Base):
    __tablename__ = "refresh_status"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    had_failures: Mapped[bool] = mapped_column(default=False)
```

**`services/stock_service.py`** (shared by dashboard/detail/portfolio)
```python
@dataclass(frozen=True)
class StockEvaluation:
    stock: Stock
    bars: list[DailyBar]
    status: Literal["ok", "insufficient_history"]
    current_price: Decimal | None       # None only if bars is empty
    change_1d_pct: Decimal | None
    indicators: Indicators | None       # None when insufficient_history
    days_available: int
    position: Position | None
    position_value: PositionValue | None
    suggestion: Suggestion | None       # None when indicators is None
    warning: Warning | None             # None when indicators is None

def evaluate_stock_snapshot(db: Session, stock: Stock, target_dollars: Decimal) -> StockEvaluation:
    """Loads DailyPrice rows -> DailyBar list. Tries calculate_indicators();
    on InsufficientHistoryError falls back to calculate_price_snapshot() for
    current_price/change_1d_pct only. Loads Trade rows -> derive_position()
    -> value_position() using current_price (works even when indicators
    aren't available — only needs the latest close). Calls
    evaluate_stock()/detect_sharp_move() only when indicators are present."""
```

**`services/trade_service.py`**
```python
class TradeValidationError(Exception): ...

@dataclass(frozen=True)
class TradeResult:
    trade: Trade
    updated_position: Position | None

def record_trade(
    db: Session, ticker: str, action: Literal["buy", "sell"],
    shares: Decimal, price_per_share: Decimal, trade_date: date,
) -> TradeResult:
    """Validates in order: ticker on watchlist; shares>0; price_per_share>0;
    trade_date not in future; for sell — position_before is not None, and
    shares <= position_before.shares_held (two distinct error messages).
    Inserts Trade, flushes, recomputes position_after over the full sorted
    history including the new trade via derive_position(). Commits."""
```

**`services/settings_service.py`**
```python
DEFAULT_TARGET = Decimal("50.00")

@dataclass(frozen=True)
class SettingsView:
    default_profit_target_dollars: Decimal
    per_position_targets: dict[str, Decimal]

def get_settings(db: Session) -> SettingsView: ...          # get-or-create id=1 row
def update_default_target(db: Session, target_dollars: Decimal) -> SettingsView: ...
def set_position_target(db: Session, ticker: str, target_dollars: Decimal) -> SettingsView: ...  # 404 via StockNotFoundError
def get_effective_target(db: Session, stock_id: int) -> Decimal: ...  # ProfitTarget override else default
```

**`api/schemas/base.py` addition**
```python
Money = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]
```

**`api/schemas/common.py`**
```python
class MetaSchema(CamelModel):
    data_as_of: datetime
    is_stale: bool
    stale_message: str | None

class SuggestionSchema(CamelModel):
    label: Literal["BUY", "WAIT", "SELL"]
    type: Literal["entry", "exit"]
    met_count: int
    total_count: int
    checklist: list[ChecklistItemSchema]
    note: str | None

    @classmethod
    def from_core(cls, s: Suggestion) -> "SuggestionSchema": ...  # derives met/total from checklist

class WarningSchema(CamelModel):
    reason: Literal["1d_move", "7d_move"]
    text: str

class ProfitTargetSchema(CamelModel):
    target_dollars: Money
    progress_dollars: Money
    remaining_dollars: Money
    reached: bool
```

**Routes** (pattern from existing `refresh.py`: plain `APIRouter()`, full inline paths, `Depends(get_db)`)
```python
# routes/stocks.py
GET  /api/stocks                 -> DashboardResponse
GET  /api/stocks/{ticker}        -> StockDetailResponse   (404 via StockNotFoundError)

# routes/portfolio.py
GET  /api/portfolio              -> PortfolioResponse

# routes/trades.py
POST /api/trades                 -> TradeResponse, 201     (422 via TradeValidationError)

# routes/settings.py
GET  /api/settings               -> SettingsResponse
PUT  /api/settings               -> SettingsResponse
PUT  /api/settings/targets/{ticker} -> SettingsResponse    (404 via StockNotFoundError)
```

**`main.py` additions**
```python
app.include_router(stocks.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(settings.router)

@app.exception_handler(RequestValidationError)
def handle_validation_error(request, exc): return JSONResponse(422, {"error": "; ".join(...)})

@app.exception_handler(TradeValidationError)
def handle_trade_error(request, exc): return JSONResponse(422, {"error": str(exc)})

@app.exception_handler(StockNotFoundError)
def handle_not_found(request, exc): return JSONResponse(404, {"error": str(exc)})
```

## Test infra (`api/tests/conftest.py`)

```python
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(os.environ["TEST_DATABASE_URL"])
    Base.metadata.create_all(engine)
    yield engine

@pytest.fixture()
def db(test_engine) -> Session:
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    session = sessionmaker(bind=test_engine)()
    yield session
    session.close()

@pytest.fixture()
def client(db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()

# + small builders: make_stock(db, ticker, company_name), make_daily_prices(db, stock, closes, volumes, start_date)
```

Requires a `TEST_DATABASE_URL` env var and a one-time local
`createdb stockmon_test`. Endpoint tests reproduce each contract JSON
example's scenario via fixtures, then assert `response.json() ==
{...expected dict...}` for the canonical case per endpoint, plus targeted
assertions for edge cases (insufficient-history, empty portfolio,
validation errors, stale meta).

## Task checklist

- [x] Migration: `refresh_status` table; `db/refresh_status.py`
- [x] `core/freshness.py` + tests
- [x] `core/dashboard.py` (sort) + tests
- [x] `core/position.py`: `ProfitTargetProgress`/`evaluate_profit_target` + tests
- [x] `core/indicators.py`: `PriceSnapshot`/`calculate_price_snapshot` + tests
- [x] `services/freshness_service.py`; wire into `routes/refresh.py`
- [x] `services/stock_service.py` (`evaluate_stock_snapshot`) + tests
- [x] `services/dashboard_service.py` + tests
- [x] `services/stock_detail_service.py` + tests
- [x] `services/portfolio_service.py` + tests
- [x] `services/settings_service.py` (incl. get-or-create) + tests
- [x] `services/trade_service.py` + tests
- [x] `api/schemas/base.py` (`Money`), `common.py`
- [x] `api/schemas/{dashboard,stock_detail,portfolio,trade,settings}.py`
- [x] `api/routes/{stocks,portfolio,trades,settings}.py`
- [x] `main.py`: include routers, register exception handlers
- [x] `tests/conftest.py` + builder helpers; document `TEST_DATABASE_URL` in `.env.example`
- [x] Endpoint tests per route matching contract JSON examples exactly
- [x] Full `pytest` run; check off Phase 3 items in `docs/plan.md`

## Implementation notes (deviations / additions beyond the plan)

- Added `core/summary.py` (`Summary`, `build_summary`) — a shared pure
  function for the totalInvested/totalCurrentValue/totalProfitLoss(Pct)
  aggregation, since both `dashboard_service` and `portfolio_service` need
  identical math (CLAUDE.md: one business rule, one function).
- **Bug caught and fixed**: Pydantic's `to_camel` alias generator converts
  `change_1d_pct` → `change1DPct` (capital D), but the contract fixes the
  field as `change1dPct` (lowercase d). Added explicit `Field(alias=...)`
  overrides on all three occurrences (`DashboardStockSchema`,
  `IndicatorsSchema`, `StockDetailResponse`). Verified every other field
  name converts correctly via `to_camel` — this was the only mismatch.
- Resolved all 13 open questions from the design phase using the proposed
  defaults (documented inline in the code/service layer): global (not
  per-ticker) staleness, ticker-alphabetical sort tiebreak, `Stock.id`
  watchlist ordering, `progressDollars` floored at 0, `daysOfHistoryRequired`
  always present, `googleFinance` link without an exchange suffix, `{"error"}`
  shape reused for 404s, real Postgres `stockmon_test` DB with
  truncate-per-test isolation.
- **Known cosmetic issue, not fixed**: every JSON request body that uses
  the existing `CamelModel` pattern (from Phase 0: `alias_generator=to_camel,
  populate_by_name=True`) triggers a Pydantic `UnsupportedFieldAttributeWarning`
  per field when FastAPI parses it, on this locked FastAPI 0.115.14 /
  Pydantic 2.13.4 pair. Confirmed cosmetic — validation and camelCase
  parsing both work correctly (see `tests/routes/`) — but it fires on every
  POST/PUT request in production too, so it's worth a follow-up look
  (possibly a FastAPI/Pydantic version bump) outside this phase.

## Open questions for you

1. **Never-refreshed / zero-bar stock** (added to watchlist, no refresh run
   yet). No contract example covers this. Proposal: treat as
   `insufficient_history` with `currentPrice`/`change1dPct` as `null`
   (requires making those two dashboard/detail fields nullable in the
   schema, a small deviation from the literal example where they're always
   numbers). OK, or would you rather exclude such stocks from the response
   entirely?
2. **`googleFinance` link exchange suffix** — no `exchange` column exists,
   and the watchlist isn't all-NASDAQ (`ORCL` is NYSE). Proposal: drop the
   suffix, link to `https://www.google.com/finance/quote/{ticker}` and
   accept the reduced accuracy for v1 (adding an `exchange` column is a
   real alternative if you'd rather do it properly now).
3. **Owned position with `insufficient_history`** (no contract example) —
   proposal: still list it on the portfolio page with `status:
   "insufficient_history"` and `suggestion: null` (current value only needs
   the latest close, not a full indicator set). OK?
4. **Dashboard sort tiebreak / watchlist ordering** — not specified by the
   contract. Proposal: ticker-alphabetical for the dashboard sort tiebreak,
   and `Stock.id` (insertion/seed order) for `GET /api/portfolio`'s
   `watchlist` list. OK?
5. **`daysOfHistoryRequired` / `tradingDaysUntilReady`** — contract labels
   them as extra fields for the insufficient-history state only. Proposal:
   include them on every detail response for one consistent schema
   (`daysOfHistoryRequired` = constant `30`, `tradingDaysUntilReady` = null
   when status is `"ok"`) rather than conditionally omitting keys. OK?
6. **Test database** — plan assumes a local `stockmon_test` Postgres
   database (created once via `createdb stockmon_test`) with
   truncate-before-each-test isolation. OK, or do you want sqlite/another
   approach despite the `daily_prices.py` Postgres-only upsert risk?
