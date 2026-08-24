# Phase 14a — Screener backend (job + cached results)

## Overview

A separate, read-only screener subsystem. `scripts/run_screener.py` is a
manually-run terminal job: it reads a plain-text ticker universe, fetches
history in batches, evaluates each ticker with the **existing** core
indicator/entry-evaluation functions (entry-only — no positions, no exit
logic), and truncate+rewrites the `screener_results` table in one
transaction. `GET /api/screener` only ever reads that cache. Shares no
data or tables with the tracked watchlist (`stocks`/`daily_prices`).

One new pure core function is needed: `price_vs_30d_avg_pct` isn't
currently exposed by `Indicators` (only `distance_from_high/low_pct`
exist), and a screener-specific "evaluate one ticker's bars, no DB, no
position" wrapper, since `stock_service.evaluate_stock_snapshot` is tied
to loading trades/position from the DB. Both go in `core/`, pure functions,
fully unit tested. No changes to `evaluate_entry`, RSI, or any existing
rule.

## Files to create/change

```
stockmon/                              (repo root)
├── screener_stocks.txt                NEW — user-edited universe, not in DB
├── api/
│   ├── src/stockmon/
│   │   ├── core/
│   │   │   ├── indicators.py          CHANGE — add price_vs_30d_avg_pct()
│   │   │   └── screener.py            NEW — pure per-ticker evaluation
│   │   ├── db/
│   │   │   └── models.py              CHANGE — add ScreenerResult model
│   │   ├── services/
│   │   │   └── screener_service.py    NEW — universe file I/O, per-ticker
│   │   │                                     fetch+evaluate, truncate+rewrite,
│   │   │                                     read-latest-run
│   │   └── api/
│   │       ├── routes/screener.py     NEW — GET /api/screener
│   │       └── schemas/screener.py    NEW — ScreenerResponse etc.
│   ├── src/stockmon/main.py           CHANGE — register screener router
│   ├── scripts/
│   │   └── run_screener.py            NEW — batching, logging, orchestrates
│   │                                        screener_service + writes DB
│   ├── alembic/versions/
│   │   └── <rev>_add_screener_results_table.py   NEW
│   └── tests/
│       ├── core/test_screener.py               NEW
│       ├── services/test_screener_service.py    NEW
│       └── routes/test_screener_route.py        NEW
└── docs/api-contract.md               already has v1.8 (no change needed)
```

## Schemas / interfaces

### `core/indicators.py` addition

```python
def price_vs_30d_avg_pct(indicators: Indicators) -> Decimal:
    """How far current_price sits from thirty_day_average, signed pct.
    Reuses the same _pct_change formula as distance_from_high/low_pct."""
    return _pct_change(indicators.thirty_day_average, indicators.current_price)
```

### `core/screener.py` (new, pure — no DB, no I/O)

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from stockmon.core.evaluation import Warning, detect_sharp_move, evaluate_entry
from stockmon.core.indicators import (
    Indicators, InsufficientHistoryError,
    calculate_indicators, calculate_price_snapshot, price_vs_30d_avg_pct,
)
from stockmon.core.market_data import DailyBar

Status = Literal["ok", "insufficient_history"]

@dataclass(frozen=True)
class ScreenerEvaluation:
    status: Status
    current_price: Decimal | None
    change_1d_pct: Decimal | None
    suggestion_label: Literal["BUY", "WAIT"] | None
    conditions_met: int | None
    conditions_total: int | None
    rsi: Decimal | None
    price_vs_30d_avg_pct: Decimal | None
    sharp_move: bool | None

def evaluate_screener_bars(bars: list[DailyBar]) -> ScreenerEvaluation:
    """bars sorted oldest-first, from a live/batch fetch (not the DB).
    Mirrors stock_service.evaluate_stock_snapshot's insufficient-history
    fallback, minus position/exit — screener stocks are never owned."""
    ...  # calculate_indicators -> entry evaluate + sharp move + price_vs_30d_avg_pct
       # InsufficientHistoryError -> calculate_price_snapshot fallback, rest None
```

### `db/models.py` addition

```python
class ScreenerResult(Base):
    """Latest screener run only -- run_screener.py truncates + rewrites
    this table in one transaction on every run. Not related to Stock;
    the screener universe is a separate, unstored ticker list."""
    __tablename__ = "screener_results"
    __table_args__ = (UniqueConstraint("ticker", name="uq_screener_result_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    change_1d_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    status: Mapped[str] = mapped_column(String(20))
    suggestion: Mapped[str | None] = mapped_column(String(4))
    conditions_met: Mapped[int | None] = mapped_column(Integer)
    conditions_total: Mapped[int | None] = mapped_column(Integer)
    rsi: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    price_vs_30d_avg_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sharp_move: Mapped[bool | None] = mapped_column(Boolean)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
```

### `services/screener_service.py`

```python
SCREENER_STOCKS_PATH = Path(__file__).resolve().parents[3] / "screener_stocks.txt"
# api/src/stockmon/services/screener_service.py -> parents[3] = repo root

@dataclass(frozen=True)
class ScreenerFetchFailure:
    ticker: str
    error: str

@dataclass(frozen=True)
class ScreenerRow:
    ticker: str
    company_name: str
    evaluation: ScreenerEvaluation

def read_screener_universe(path: Path = SCREENER_STOCKS_PATH) -> list[str]:
    """One ticker per line, blank lines ignored, uppercased, stripped."""

def fetch_and_evaluate_ticker(provider: MarketDataProvider, ticker: str) -> ScreenerRow | ScreenerFetchFailure:
    """History fetch failure -> skip (Failure). Company-name fetch failure
    after a successful history fetch -> fall back to the ticker string as
    company_name (row still succeeds -- the name is cosmetic, the analysis
    isn't); logs a quiet "<ticker>: name unavailable, using symbol" line so
    a systematically-nameless run is still noticeable in the terminal
    output. Only a history-fetch failure skips a ticker."""

def save_screener_run(db: Session, rows: list[ScreenerRow], run_at: datetime) -> None:
    """Truncate + bulk insert in one transaction (DELETE then INSERT,
    single commit -- mirrors the "one transaction" requirement; no
    ON CONFLICT needed since the table is always fully rewritten)."""

@dataclass(frozen=True)
class ScreenerRun:
    run_at: datetime | None
    rows: list[ScreenerResult]  # ORM rows, mapped to schema at the API edge

def get_latest_screener_run(db: Session) -> ScreenerRun:
    """Empty table -> ScreenerRun(run_at=None, rows=[])."""
```

### `scripts/run_screener.py`

```python
BATCH_SIZE = 10
BATCH_PAUSE_SECONDS = 1.5

def main() -> None:
    tickers = read_screener_universe()
    print(f"Screener run starting: {len(tickers)} tickers, batch size {BATCH_SIZE}")
    rows: list[ScreenerRow] = []
    failures: list[ScreenerFetchFailure] = []
    for batch in _chunks(tickers, BATCH_SIZE):
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            for result in pool.map(lambda t: fetch_and_evaluate_ticker(provider, t), batch):
                (rows if isinstance(result, ScreenerRow) else failures).append(result)
        print(f"[{len(rows) + len(failures)}/{len(tickers)}] done")
        time.sleep(BATCH_PAUSE_SECONDS)

    db = SessionLocal()
    try:
        run_at = datetime.now().astimezone()
        save_screener_run(db, rows, run_at)
    finally:
        db.close()

    print(f"Screener run complete: {len(rows)} succeeded, {len(failures)} failed")
    if failures:
        print("Failed: " + ", ".join(f"{f.ticker} ({f.error})" for f in failures))
```

### `api/schemas/screener.py`

```python
class ScreenerResultSchema(CamelModel):
    ticker: str
    company_name: str
    current_price: Money | None
    change_1d_pct: Money | None = Field(alias="change1dPct")
    suggestion: Literal["BUY", "WAIT"] | None
    met_count: int | None
    total_count: int | None
    rsi: Money | None
    price_vs_30d_avg_pct: Money | None
    sharp_move: bool | None
    status: Literal["ok", "insufficient_history"]

class ScreenerResponse(CamelModel):
    meta: MetaSchema
    run_at: datetime | None
    results: list[ScreenerResultSchema]
```

`GET /api/screener` reuses `get_freshness(db)` for `meta` (same shared
convention as every other endpoint — tied to the main watchlist's
refresh_status, not the screener's own run_at, which is its own field).

## Tasks

- [x] `core/indicators.py`: add `price_vs_30d_avg_pct()` + test
- [x] `core/screener.py`: `ScreenerEvaluation` + `evaluate_screener_bars()`,
      covering ok / insufficient_history (with partial bars) / zero bars
- [x] `db/models.py`: `ScreenerResult` model
- [x] Alembic migration: create `screener_results` table
- [x] `screener_stocks.txt` at repo root with 5 example tickers
- [x] `services/screener_service.py`: universe read, per-ticker
      fetch+evaluate, `save_screener_run` (truncate+rewrite, one
      transaction), `get_latest_screener_run`
- [x] `scripts/run_screener.py`: batch constants, `ThreadPoolExecutor`
      concurrency within a batch, sequential batches with pause, progress
      logging, summary + failed-ticker names
- [x] `api/schemas/screener.py` + `api/routes/screener.py`: `GET /api/screener`
- [x] Register router in `main.py`
- [x] Tests: core (entry-only eval, insufficient-history fallback, zero
      bars), service (fetch failure skipped not fatal, truncate+rewrite
      replaces prior run, never-run state), route (latest-run shape,
      never-run empty state per contract) — 230 passed

## Decisions (resolved)

1. **Company-name fetch fails after a successful history fetch** — fall
   back to the ticker symbol as `company_name`, row still succeeds; log a
   quiet "`<ticker>`: name unavailable, using symbol" line. Only a
   history-fetch failure skips a ticker.
2. **`sharpMove` on `insufficient_history` rows** — null, same dependency
   on indicators as RSI. A boolean `false` would falsely assert "no sharp
   move" when the truth is "not enough data to know."
3. **History fetch window** — reuse `refresh_service.DEFAULT_HISTORY_DAYS`
   (60 days), same as the tracked watchlist. No separate screener constant.
4. **`current_price` fetch source** — last close from `fetch_daily_history`,
   no separate live quote. Consistent with the rest of the app; `run_at`
   already tells the user how stale the batch is.
