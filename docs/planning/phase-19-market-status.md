# Phase 19 — Market status indicator

## Context

Phase 18 made `currentPrice` reflect a live quote on refresh, but that only
works when there's actually a trading session happening — pre-market,
after-hours, weekends, and holidays there's nothing new to fetch, and the
chart/dashboard correctly keep showing the last close. Without any signal
for *why*, that looks like a bug ("today's data is missing"). This phase
adds a small, clock-based market-status indicator next to the existing
freshness timestamp so the gap is self-explanatory.

Computed purely from the current time (NYSE regular hours, Eastern time) —
not from yfinance — so it's always exact and never lags behind the last
refresh the way a data-derived status would.

## Files to create/change

```
api/src/stockmon/
├── core/
│   ├── market_hours.py          (NEW: get_market_status pure function)
│   └── freshness.py             (Freshness gains market_status; build_freshness computes it)
├── services/
│   └── freshness_service.py     (passes `now` through to get_market_status)
├── api/schemas/
│   └── common.py                (MetaSchema gains marketStatus + marketStatusText)
api/tests/core/
├── test_market_hours.py         (NEW)
└── test_freshness.py            (extend: market_status passthrough)
docs/
├── api-contract.md              (meta block gains 2 fields; changelog v1.12)
└── plan.md                      (Phase 19 entry)
ui/src/
├── api/types.js                 (Meta JSDoc typedef gains marketStatus/marketStatusText)
└── components/layout/
    ├── MarketStatusBadge.jsx    (NEW: dot + text, colored by state)
    └── FreshnessBar.jsx         (renders MarketStatusBadge alongside the timestamp)
```

## Schema / interfaces

**`core/market_hours.py` (new, pure, no I/O):**

```python
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

MarketState = Literal["open", "pre_market", "after_hours", "closed_weekend", "closed_holiday"]

# NYSE full-closure holidays. Source: NYSE Group's official 2025/2026/2027
# holiday calendar (theice.com press release, Nov 2024). Needs a manual
# top-up once 2028 approaches -- there's no library dependency for this,
# it's a short fixed list refreshed ~once a year.
US_MARKET_HOLIDAYS: set[date] = {
    # 2025
    date(2025, 1, 1), date(2025, 1, 20), date(2025, 2, 17), date(2025, 4, 18),
    date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 4), date(2025, 9, 1),
    date(2025, 11, 27), date(2025, 12, 25),
    # 2026
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3),
    date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7),
    date(2026, 11, 26), date(2026, 12, 25),
    # 2027
    date(2027, 1, 1), date(2027, 1, 18), date(2027, 2, 15), date(2027, 3, 26),
    date(2027, 5, 31), date(2027, 6, 18), date(2027, 7, 5), date(2027, 9, 6),
    date(2027, 11, 25), date(2027, 12, 24),
}

_LABELS: dict[MarketState, str] = {
    "open": "Market Open",
    "pre_market": "Pre-Market Open",
    "after_hours": "After Hours",
    "closed_weekend": "Market Closed",
    "closed_holiday": "Market Closed",
}


@dataclass(frozen=True)
class MarketStatus:
    state: MarketState
    label: str


def get_market_status(now: datetime) -> MarketStatus:
    """NYSE regular-hours check only (9:30am-4pm ET, Mon-Fri, minus
    holidays) -- no pre/post-market session distinction beyond that, no
    early-close-day handling (rare, cosmetic only)."""
    ny_now = now.astimezone(NY_TZ)
    if ny_now.weekday() >= 5:
        state: MarketState = "closed_weekend"
    elif ny_now.date() in US_MARKET_HOLIDAYS:
        state = "closed_holiday"
    elif ny_now.time() < MARKET_OPEN:
        state = "pre_market"
    elif ny_now.time() >= MARKET_CLOSE:
        state = "after_hours"
    else:
        state = "open"
    return MarketStatus(state=state, label=_LABELS[state])
```

**`core/freshness.py` — extend `Freshness`:**

```python
@dataclass(frozen=True)
class Freshness:
    data_as_of: datetime
    is_stale: bool
    stale_message: str | None
    market_status: MarketStatus   # NEW

def build_freshness(now, last_attempted_at, last_succeeded_at, had_failures) -> Freshness:
    market_status = get_market_status(now)
    ...  # existing branches, each return gains market_status=market_status
```

**`api/schemas/common.py` — extend `MetaSchema`:**

```python
class MetaSchema(CamelModel):
    data_as_of: datetime
    is_stale: bool
    stale_message: str | None
    market_status: Literal["open", "pre_market", "after_hours", "closed_weekend", "closed_holiday"]
    market_status_text: str

    @classmethod
    def from_core(cls, freshness: Freshness) -> "MetaSchema":
        return cls(
            data_as_of=freshness.data_as_of,
            is_stale=freshness.is_stale,
            stale_message=freshness.stale_message,
            market_status=freshness.market_status.state,
            market_status_text=freshness.market_status.label,
        )
```

Machine enum + backend-owned display text, matching the existing
`suggestion`/checklist convention — UI never re-derives wording.

**Contract (`docs/api-contract.md`) — `meta` block, v1.12:**

```json
{
  "meta": {
    "dataAsOf": "2026-08-27T09:15:00-04:00",
    "isStale": false,
    "staleMessage": null,
    "marketStatus": "pre_market",
    "marketStatusText": "Pre-Market Open"
  }
}
```

Additive only — every existing `meta` consumer keeps working unchanged;
new fields simply appear on every GET response that already includes `meta`.

## UI

**`MarketStatusBadge.jsx` (new, small):**

```jsx
export function MarketStatusBadge({ marketStatus, marketStatusText }) {
  if (!marketStatus) return null;
  const dotClass = marketStatus === "open" ? "bg-good" : "bg-neutral";
  return (
    <div className="flex items-center gap-2 whitespace-nowrap text-xs text-ink-muted">
      <span className={`h-[7px] w-[7px] flex-none rounded-full ${dotClass}`} />
      <span>{marketStatusText}</span>
    </div>
  );
}
```

`FreshnessBar.jsx` renders it next to the existing timestamp (both read
from the same `meta` prop it already receives — no new fetch, no new page
wiring). Shows up everywhere `FreshnessBar` already does: the app header
and per-page detail headers.

## Tasks

- [x] `core/market_hours.py`: `get_market_status` pure function + holiday set
- [x] `api/tests/core/test_market_hours.py`: one test per state (open,
      pre-market, after-hours, weekend, holiday) + boundary times (9:30
      exactly, 16:00 exactly)
- [x] `core/freshness.py`: `Freshness` gains `market_status`; `build_freshness`
      computes it via `get_market_status(now)`
- [x] `api/tests/core/test_freshness.py`: extend existing cases to assert
      `market_status` is populated correctly
- [x] `api/schemas/common.py`: `MetaSchema` gains `market_status` /
      `market_status_text`, wired in `from_core`
- [x] `docs/api-contract.md`: `meta` block gains the two fields; changelog v1.12
- [x] `docs/plan.md`: Phase 19 entry
- [x] `ui/src/api/types.js`: `Meta` JSDoc typedef gains the two fields
- [x] `ui/src/components/layout/MarketStatusBadge.jsx` (new)
- [x] `ui/src/components/layout/FreshnessBar.jsx`: render the badge next to
      the timestamp

## Verification

1. `pytest` in `api/` — new + existing tests green.
2. Manual: with the backend restarted, load the dashboard right now
   (pre-market) and confirm the header shows "Pre-market" next to "Data as
   of ...". Check back after 9:30 AM ET and confirm it flips to "Market
   open", and again after 4:00 PM ET for "After hours".
3. Manual: temporarily fake `now` (or just reason about it) to sanity-check
   a Saturday shows "closed — weekend" and Dec 25, 2026 shows "closed —
   holiday".

## Decisions

- Wording: `open` → "Market Open", `pre_market` → "Pre-Market Open",
  `after_hours` → "After Hours", `closed_weekend`/`closed_holiday` → both
  display as "Market Closed" (machine enum still distinguishes the two
  underlying states; only the display text collapses them).
- Confirmed: extend the shared `meta` block (contract v1.12, additive-only).
