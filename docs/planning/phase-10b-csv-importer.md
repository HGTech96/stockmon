# Phase 10b — CSV History Importer

## Overview

A standalone script, `api/scripts/import_history.py` (invoked directly like
`seed_watchlist.py` / `reset_to_initial_state.py` — **not** a migration, no
DB schema change). It bulk-loads one ordered CSV of past deposits/
withdrawals/buys/sells into an already-populated DB (top-up, not a fresh
seed).

Columns: `date,type,ticker,shares,price,amount`. `type` is one of
`deposit,withdraw,buy,sell`; `ticker`/`shares`/`price` apply to buy/sell,
`amount` applies to deposit/withdraw, blank otherwise. Dates are ISO
`YYYY-MM-DD` (confirmed against the sample `portfolio.csv` at the repo root).

**Design decision: no new core function.** Same reasoning as Phase 8
(`derive_position` reused as-is for the oversell rule). Here the two
existing sequence-validators are reused unchanged:
- `derive_position` (per ticker) — cumulative sells never exceed shares held.
- `validate_cash_sequence` / `derive_cash_balance` (global, all tickers +
  cash events, `chronological_key` ordering) — cash never goes negative.

The importer's job is orchestration, not new business rules: parse the CSV,
replay each row through those two existing validators on top of the
current DB state, and only commit if every row survives. This orchestration
is a **service**, not a core function.

**Duplicate scope (confirmed with user):** a row is rejected as a duplicate
if it exactly matches (all six fields) either an *existing DB row* or an
*earlier row already parsed from the same CSV*. Catches both re-imports and
copy-paste errors within the source file.

**Extraneous fields (confirmed with user):** ignored, not rejected — only
the fields relevant to a row's `type` are read (e.g. a populated `ticker` on
a `deposit` row is silently ignored).

## Validation strategy: two-pass, all in memory first

1. Pass 1 (no DB writes): load existing trades (grouped by ticker) and
   existing cash events from the DB once, plus build duplicate-check sets
   for both existing-DB-row and within-CSV cases. Walk the CSV rows in file
   order, maintaining a running per-ticker trade-event list and a running
   global cash-flow-event list (seeded from the existing DB data). For each
   row: check it's not a duplicate of an existing DB row, then not a
   duplicate of an earlier row already parsed from this CSV; build its
   candidate event; append to the relevant running list(s); re-run
   `derive_position` (buy/sell) and/or `validate_cash_sequence`
   (all four types) against the updated list. Any failure (parse error,
   unknown ticker, either duplicate case, `PositionError`, `CashError`)
   raises immediately, naming the CSV line number and reason. Nothing has
   touched the DB yet.
2. Pass 2 (only if pass 1 fully succeeds): construct all `Trade` /
   `CashEvent` rows and add them in one session, one `commit()`. Atomicity
   falls out of this ordering for free — no rollback logic needed.

## Files to create/change

```
api/src/stockmon/
  services/import_service.py     (new: parse_csv_rows, import_rows,
                                   ImportRow, ImportSummary, ImportError)
api/scripts/
  import_history.py              (new: thin CLI — open file, call
                                   import_service, print summary or error)
api/tests/
  services/test_import_service.py  (new)
```

No changes to `core/`, `db/models.py`, API routes, or the frontend.

## Schemas / interfaces

**services/import_service.py**

```python
@dataclass(frozen=True)
class ImportRow:
    line: int  # 1-based CSV line number (header = line 1), for error messages
    event_date: date
    kind: Literal["deposit", "withdraw", "buy", "sell"]
    ticker: str | None
    shares: Decimal | None
    price_per_share: Decimal | None
    amount: Decimal | None


class ImportError(Exception):
    """Message always names the offending line number and reason. Raised on
    any parse error, unknown ticker, either duplicate case, PositionError, or
    CashError — the whole import aborts, nothing is written."""


@dataclass(frozen=True)
class ImportSummary:
    trades_added: int
    cash_events_added: int


def parse_csv_rows(fileobj) -> list[ImportRow]:
    """Reads the header + all data rows, parses/validates per-row shape
    (kind is one of the four; required fields for that kind present and
    parseable as Decimal/date; extraneous fields ignored). Raises
    ImportError naming the line on any parse problem. Does not touch the DB
    (no ticker-exists check here — that needs a session, done in
    import_rows)."""


def import_rows(db: Session, rows: list[ImportRow]) -> ImportSummary:
    """Pass 1: replays each row against current DB state via derive_position
    (per ticker, imported from core.position) and validate_cash_sequence
    (global, imported from services.cash_service), plus duplicate checks
    against both the pre-import DB snapshot and earlier rows in this CSV.
    Raises ImportError on the first failure, before any write. Pass 2: only
    on full success, inserts every Trade/CashEvent row and commits once."""
```

**api/scripts/import_history.py**

```python
def main() -> None:
    """argv[1] = CSV path. Opens SessionLocal(), calls parse_csv_rows then
    import_rows, prints a one-line summary on success ("Imported N trades,
    M cash events") or the ImportError message and exits 1 on failure —
    same shape as seed_watchlist.py's print-and-close pattern."""
```

## Tasks

- [x] `ImportRow` / `ImportSummary` / `ImportError` + `parse_csv_rows` in
      `import_service.py` (header + shape validation, ISO dates, line-numbered
      errors, extraneous fields ignored)
- [x] `import_rows`: load existing trades-by-ticker + cash events once; build
      duplicate-check sets for both existing-DB-row and within-CSV cases
      (six-field exact match); per-row candidate event + re-validate via
      `derive_position` / `validate_cash_sequence`; abort with line-numbered
      `ImportError` on first failure; commit everything only after every
      row passes
- [x] `import_history.py` CLI script (mirrors `seed_watchlist.py` style)
- [x] Tests in `test_import_service.py`:
      - valid mixed sequence (deposit, buy, sell, withdraw, another buy)
        imports cleanly, position/cash match expectations afterward
      - a row that oversells cash (buy with insufficient funds) → abort,
        `ImportError` names the correct line, DB unchanged (row count same
        before/after)
      - a row that oversells shares (sell more than held) → abort, named,
        DB unchanged (extra coverage beyond the original ask)
      - a row exactly duplicating an existing DB row → abort, named, DB
        unchanged
      - a row exactly duplicating an earlier row in the same CSV → abort,
        named, DB unchanged
      - a fractional-share buy row imports with exact Decimal shares
      - importing on top of a non-empty DB (existing trades/cash present)
        correctly continues the replay rather than starting fresh
      - unknown ticker → abort, named, DB unchanged

All 8 tests pass; full suite (205 tests) passes with no regressions.

## Manual smoke-test note

Running `import_history.py` against the sample `portfolio.csv` at the repo
root correctly aborted at line 3: the file's deposit is dated 2026-08-01,
but the first buy is dated 2026-06-10 — by real calendar date (not file
order — `validate_cash_sequence` sorts by actual date via
`chronological_key`), that buy has no funding yet. This is the importer
working as designed, not a bug; the CSV's deposit date likely needs
correcting before a real import.

## Resolved questions

1. **Duplicate scope.** Also reject exact duplicates within the same CSV
   file, in addition to matches against existing DB rows.
2. **Strictness of blank fields.** Ignore irrelevant populated fields (only
   read fields required for that row's `type`).
3. **CSV date format.** ISO `YYYY-MM-DD`, confirmed by `portfolio.csv`.
