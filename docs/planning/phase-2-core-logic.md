# Phase 2 — Core Logic

## Context

Phases 0–1 built the FastAPI skeleton, DB models, and the data-refresh
pipeline. `core/` currently holds only `market_data.py` (`DailyBar`, `Quote`,
`MarketDataProvider` ABC) — no indicator, evaluation, or position logic
exists yet. `daily_prices` rows are populated (≈60 days per ticker via
`refresh_all_stocks`), so the inputs Phase 2 needs are already in the DB;
this phase does not touch `services/`, `api/`, or the DB — pure functions
in `core/` only, per `CLAUDE.md`.

Phase 2 implements every business rule fixed by `docs/api-contract.md`:
indicator math (14-period Wilder RSI + the 12 indicators from
`docs/product-spec.md`), the entry checklist (BUY/WAIT), the exit checklist
(SELL/WAIT), the owned-stock precedence rule, the sharp-move warning, and
position derivation from trades (event-sourced, weighted-average cost).
These become the single source of truth the API layer (Phase 3) will call.

Verified from the codebase:
- `core/market_data.py`: `DailyBar(date, open, high, low, close, volume)` —
  this is the input type for indicator calculations.
- `db/models.py`: no `positions` table — confirms derivation-only.
  `Trade.shares`/`price_per_share` are `Numeric(12,4)` (fractional shares
  allowed), `action` is `'buy'|'sell'`.
- Phase 1 decision (`docs/planning/phase-1-data-layer.md`): "current price"
  reads the latest `daily_prices` row, not a live quote — Phase 2 follows
  the same convention (`bars[-1].close`).
- `pandas`/`numpy` are only transitive deps of `yfinance`, not declared —
  indicator math is implemented over plain `list[DailyBar]` + `Decimal`,
  stdlib only, consistent with `core/` rules and the `DailyBar` dataclass
  already being plain (not a DataFrame).
- Test pattern established in `tests/services/test_refresh_service.py`:
  fake ABC implementations, small fixture-building helpers, plain asserts.
  Phase 2 tests need neither `MagicMock` nor a DB — pure dataclass in/out.

## Design decisions

- **Indicator window**: 30-day average/high/low/volume use exactly the
  last 30 bars. RSI uses the *entire* bar list passed in (better Wilder
  smoothing when more history is available), not just the 30-bar window.
  `MIN_HISTORY_DAYS = 30` gates the whole `Indicators` calculation —
  fewer than 30 bars raises `InsufficientHistoryError` (this is what the
  API layer will catch in Phase 3 to set `status: "insufficient_history"`).
- **1-day / 7-day change**: trading-day offsets, not calendar days
  (`bars[-1]` vs `bars[-2]` / `bars[-8]`), since the data is one row per
  trading day.
- **RSI**: standard 14-period Wilder — seed with the simple average of the
  first 14 gains/losses, then Wilder-smooth (`avg = (prev*13 + new)/14`)
  over the rest. `avg_loss == 0` → RSI = 100; `avg_gain == 0` → RSI = 0.
- **Zero-volume guard**: if 30-day average volume is 0, `volumeVsAveragePct`
  is defined as `0` and `volume_above_avg` is `False` (avoids
  division-by-zero; a real stock at 0 average volume is a degenerate case
  but shouldn't crash evaluation).
- **Position math**: `derive_position` replays `TradeEvent`s in the order
  given (caller sorts by `trade_date`, then insertion order for same-day
  trades) using the weighted-average-cost rule from the contract. Reopening
  a closed position (buy after shares hit 0) works for free — the formula
  naturally resets `avg_price` when `shares` was 0. A sell that exceeds
  shares-held-at-that-point raises `PositionError` (defensive; Phase 3's
  trade-validation endpoint can reuse this same function/exception rather
  than re-implementing the "oversell" check).
- **Precedence + note**: per the contract's "the returned checklist is the
  one belonging to the winning label" — the `note` (used only for
  "profit target reached but no technical confirmed" → WAIT) is attached
  **only** when the exit checklist is the one being returned (SELL, or
  WAIT on an owned stock). If entry BUY wins precedence over an exit WAIT,
  no note is attached, even if the exit evaluation internally had one.
- **Sharp-move text**: contract shows one example string for `1d_move`;
  assumed the same generic text is used for `7d_move` (reason field is
  what differs). If both trigger, `1d_move` takes precedence (checked
  first).

## Files to create/change

```
api/src/stockmon/core/
├── market_data.py        (existing, untouched)
├── indicators.py         NEW — Indicators, calculate_indicators(), InsufficientHistoryError
├── position.py           NEW — TradeEvent, Position, PositionValue, derive_position(),
│                                value_position(), PositionError
└── evaluation.py         NEW — ChecklistItem, Suggestion, Warning, evaluate_entry(),
                                 evaluate_exit(), evaluate_stock(), detect_sharp_move()

api/tests/core/
├── __init__.py            (existing, empty)
├── test_indicators.py     NEW
├── test_position.py       NEW
└── test_evaluation.py     NEW
```

## Schemas / interfaces

**`core/indicators.py`**

```python
MIN_HISTORY_DAYS = 30
RSI_PERIOD = 14

class InsufficientHistoryError(Exception):
    def __init__(self, available: int, required: int = MIN_HISTORY_DAYS): ...

@dataclass(frozen=True)
class Indicators:
    current_price: Decimal
    change_1d_pct: Decimal
    change_7d_pct: Decimal
    thirty_day_average: Decimal
    thirty_day_high: Decimal
    thirty_day_low: Decimal
    distance_from_high_pct: Decimal   # <= 0
    distance_from_low_pct: Decimal    # >= 0
    rsi: Decimal
    todays_volume: int
    average_volume: Decimal
    volume_vs_average_pct: Decimal

def calculate_indicators(bars: list[DailyBar]) -> Indicators:
    """bars sorted oldest-first. Raises InsufficientHistoryError if
    len(bars) < MIN_HISTORY_DAYS."""

def _wilder_rsi(closes: list[Decimal], period: int = RSI_PERIOD) -> Decimal: ...
```

**`core/position.py`**

```python
@dataclass(frozen=True)
class TradeEvent:
    action: Literal["buy", "sell"]
    shares: Decimal
    price_per_share: Decimal
    date: date

class PositionError(Exception):
    """Sell exceeds shares held at that point in the trade history."""

@dataclass(frozen=True)
class Position:
    shares_held: Decimal
    avg_purchase_price: Decimal
    amount_invested: Decimal

@dataclass(frozen=True)
class PositionValue:
    current_value: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal

def derive_position(trades: list[TradeEvent]) -> Position | None:
    """Chronological replay, weighted-average cost. Returns None if net
    shares held is 0 (never bought, or fully sold — 'closed')."""

def value_position(position: Position, current_price: Decimal) -> PositionValue: ...
```

**`core/evaluation.py`**

```python
RSI_LOW, RSI_HIGH = Decimal(40), Decimal(70)
NEAR_LOW_PCT, NEAR_HIGH_PCT = Decimal(5), Decimal(5)
SHARP_1D_PCT, SHARP_7D_PCT = Decimal(5), Decimal(10)
ENTRY_BUY_MIN_PASSING = 3

@dataclass(frozen=True)
class ChecklistItem:
    id: str
    text: str
    passed: bool

@dataclass(frozen=True)
class Suggestion:
    label: Literal["BUY", "WAIT", "SELL"]
    type: Literal["entry", "exit"]
    checklist: list[ChecklistItem]
    note: str | None

@dataclass(frozen=True)
class Warning:
    reason: Literal["1d_move", "7d_move"]
    text: str

def evaluate_entry(indicators: Indicators) -> Suggestion:
    """price_below_30d_avg, near_30d_low, rsi_low, volume_above_avg.
    BUY if >= 3 pass, else WAIT."""

def evaluate_exit(indicators: Indicators, position_value: PositionValue,
                   target_dollars: Decimal) -> Suggestion:
    """profit_target_reached, rsi_high, near_30d_high.
    SELL if profit_target_reached AND >=1 technical passes.
    profit_target_reached alone -> WAIT + note. Never SELL at a loss
    (profit_target_reached is False whenever profit_loss < target)."""

def evaluate_stock(indicators: Indicators, position_value: PositionValue | None,
                    target_dollars: Decimal) -> Suggestion:
    """position_value is None -> entry only. Otherwise runs both and
    applies precedence: exit SELL > entry BUY > WAIT (exit checklist)."""

def detect_sharp_move(indicators: Indicators) -> Warning | None:
    """>5% 1-day move -> '1d_move' (checked first); else >10% 7-day
    move -> '7d_move'; else None."""
```

## Task list

- [x] `core/indicators.py`: `Indicators`, `calculate_indicators()`, `_wilder_rsi()`, `InsufficientHistoryError`
- [x] `core/position.py`: `TradeEvent`, `Position`, `PositionValue`, `derive_position()`, `value_position()`, `PositionError`
- [x] `core/evaluation.py`: `ChecklistItem`, `Suggestion`, `Warning`, `evaluate_entry()`, `evaluate_exit()`, `evaluate_stock()`, `detect_sharp_move()`
- [x] `tests/core/test_indicators.py`:
  - hand-computed example locks the exact Wilder RSI formula
  - property checks: all-gains → RSI 100, all-losses → RSI 0
  - insufficient history (< 30 bars) raises `InsufficientHistoryError`
  - zero volume today, and zero 30-day average volume (no crash, defined result)
  - 1d/7d change, 30d avg/high/low, distance-from-high/low against hand-built fixtures
- [x] `tests/core/test_position.py`:
  - buy then buy → weighted average recomputed
  - buy then partial sell → shares/invested reduced proportionally, avg price unchanged
  - buy then sell all shares → position closed (`None`)
  - sell after a close, followed by a new buy → reopens correctly (avg price resets)
  - oversell (sell > shares held at that point) → `PositionError`
  - `value_position`: profit case and loss case (negative `profit_loss`/`profit_loss_pct`)
- [x] `tests/core/test_evaluation.py`:
  - entry: 4/4, 3/4, 2/4, 0/4 passing → BUY/BUY/WAIT/WAIT
  - exit: target+technical → SELL; target alone → WAIT + note; technical alone (no target) → WAIT, no note; loss position → never SELL
  - precedence: not owned → entry only; owned + exit SELL → SELL wins over entry BUY; owned + exit WAIT + entry BUY → BUY wins, `type: "entry"`; owned + both WAIT → `type: "exit"` (note attached only if the underlying exit had one)
  - warning: 1d boundary (exactly 5% does not trigger, >5% does), 7d boundary (exactly 10% / >10%), both triggered → `1d_move` wins, neither → `None`
- [x] Run `pytest` for the whole suite, confirm all core tests pass alongside existing Phase 0/1 tests — 42 passed
- [x] Check off Phase 2 items in `docs/plan.md`

## Open questions

1. **Exit checklist wording** — `docs/api-contract.md` gives exact `text`
   strings for the entry checklist but not for exit (`profit_target_reached`,
   `rsi_high`, `near_30d_high`). Planned copy: "Profit target has been
   reached", "RSI is relatively high (`<value>`)", "Price is close to its
   30-day high". Confirm or adjust wording.
2. **Sharp-move text** — assumed identical text for both `1d_move` and
   `7d_move` reasons (contract only shows one example). Confirm.
3. **RSI window** — using the *entire* supplied bar list (not just the
   last 30) for Wilder smoothing accuracy, while every other indicator
   uses exactly 30. Confirm that's intended, or should RSI also be
   pinned to a fixed 30-bar window for simplicity/determinism?
4. **Precedence + note** — when entry BUY wins over an owned stock's exit
   WAIT that had a "target reached" note, the plan drops the note (since
   the winning checklist is entry's, not exit's). Confirm this reading.
5. **Oversell defensiveness** — `derive_position` raising `PositionError`
   is meant to double as the reusable check for Phase 3's
   "sell more than currently held" trade validation. Confirm that's a
   welcome coupling rather than scope creep for this phase.

---

**Status: approved via plan-mode review on 2026-08-19. Implemented same day.**
