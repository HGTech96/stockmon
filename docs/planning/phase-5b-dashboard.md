# Phase 5b — Dashboard Page

## Overview

Build the real Dashboard page (`/`), replacing the Phase 4 JSON-dump
placeholder, from `GET /api/stocks`. Matches `design/reference/.../dashboard-src.html`'s
`#page-dashboard` layout: page head, summary strip (hidden when no trades),
watchlist table with server-provided ordering only (no client sort/filter),
rows that navigate to the stock detail route.

Two components get extracted/promoted to shared this session because
Dashboard needs logic that currently only lives inside 5a's `DetailHeader`:
`Trend` (the arrow + colored 1-day-change text) is pulled out into its own
shared component so Dashboard rows and the detail header use the exact same
code instead of Dashboard reimplementing it. `SummaryStrip` is built shared
from the start since Portfolio needs the identical three-tile block next
session (same `Summary` shape in both contracts). `SuggestionBadge` from 5a
is reused as-is (`size="sm"`, same `INSUFFICIENT`-on-status convention
already established there).

## Files to create/change

```
ui/src/
├── components/
│   ├── trend/
│   │   └── Trend.jsx                 NEW — extracted from DetailHeader.jsx (5a)
│   └── summary/
│       └── SummaryStrip.jsx          NEW — shared (Portfolio reuses next session)
└── pages/
    ├── stock-detail/
    │   └── DetailHeader.jsx          CHANGE — use the extracted <Trend/> instead of its own copy
    └── dashboard/
        ├── DashboardPage.jsx         REWRITE
        ├── StockTable.jsx            NEW — table shell + header row
        └── StockRow.jsx              NEW — one clickable row
```

## Schemas / interfaces

**`components/trend/Trend.jsx`**
```jsx
/**
 * @param {{ change1dPct: number|null }} props
 * Arrow icon + colored fmtPct text: green/up when > 0.05, red/down when
 * < -0.05, gray/flat (no icon) otherwise; "–" via fmtOrDash when null.
 * Identical to what DetailHeader (5a) had inline -- extracted so Dashboard
 * rows don't reimplement the same direction/color logic.
 */
export function Trend({ change1dPct }) { ... }
```

**`components/summary/SummaryStrip.jsx`**
```jsx
/**
 * @param {{ summary: import('../../api/types').Summary }} props
 * Three tiles: Total invested, Total current value, Total profit/loss (with
 * its % as a colored sub-line). Caller decides whether to render this at
 * all -- both contracts (`GET /api/stocks`, `GET /api/portfolio`) send
 * `summary: null` when no trades are recorded, and this component doesn't
 * special-case that; it just isn't mounted.
 */
export function SummaryStrip({ summary }) { ... }
```

**`pages/dashboard/StockRow.jsx`**
```jsx
/**
 * @param {{ stock: import('../../api/types').DashboardStock }} props
 * One row, click or Enter/Space navigates to `/stocks/{ticker}` (matches
 * the reference's keyboard-accessible clickable rows). Warning triangle
 * icon before the ticker when `stock.warning` is set.
 *
 * Price and 1-day change (<Trend/>) always render the real values the API
 * sent -- never dashed, even when `status === "insufficient_history"`
 * (the contract sends real numbers there; a stock trades and has a real
 * daily change regardless of how much history is on file).
 *
 * Suggestion column: `<SuggestionBadge label={stock.suggestion} size="sm"/>`
 * when `status === "ok"`; when `status === "insufficient_history"`, plain
 * muted text "Not enough data" -- deliberately *not* the badge component,
 * per your call that this state shouldn't carry badge chrome on the
 * dashboard (differs from the detail page's large INSUFFICIENT *badge*,
 * which you already approved in 5a -- that's a distinct, larger context).
 *
 * P/L cell renders "–" when `position` is null (not owned, or insufficient
 * history -- both send `position: null`).
 */
export function StockRow({ stock }) { ... }
```

**`pages/dashboard/StockTable.jsx`**
```jsx
/**
 * @param {{ stocks: import('../../api/types').DashboardStock[] }} props
 * Table shell (Stock / Price / 1-day change / Suggestion / My P/L header
 * row) + one <StockRow/> per entry, rendered in exactly the order the array
 * arrives in. The contract guarantees server-side ordering (SELL, BUY,
 * warnings, WAIT, then insufficient-history) -- this component does not
 * sort, filter, or re-rank.
 */
export function StockTable({ stocks }) { ... }
```

**`DashboardPage.jsx`** — composition, no new business logic:
- loading: centered "Loading…" text (matches StockDetailPage's pattern)
- error: centered error message from the thrown `Error`
- page head: "Dashboard" + `{stocks.length}-stock watchlist · stocks needing attention are sorted to the top`
- `{data.summary && <SummaryStrip summary={data.summary} />}` (no-positions state: summary is `null`, tiles just don't render)
- `<StockTable stocks={data.stocks} />`

## Task list

- [x] Extract `components/trend/Trend.jsx` out of `DetailHeader.jsx`; refactor `DetailHeader` to import and use it
- [x] `components/summary/SummaryStrip.jsx`
- [x] `pages/dashboard/StockRow.jsx` (click + keyboard nav to `/stocks/:ticker`, warning icon, badge, P/L dash)
- [x] `pages/dashboard/StockTable.jsx`
- [x] Rewrite `pages/dashboard/DashboardPage.jsx`
- [x] Manual check via `claude-in-chrome` against the real backend: default (has trades → summary visible), a warning-flagged row, an insufficient-history row, row click navigates to the correct detail page, loading — see implementation notes for two states that weren't re-verified live
- [x] Check off "Dashboard page" under Phase 5 in `docs/plan.md`

## Decisions from review

1. **Insufficient-history row, 1-day change column**: render the real
   `change1dPct` — the mock's dash was wrong, it hid true information the
   backend actually sent (the stock has a real price and daily change
   regardless of history length). Dash only what's actually null:
   Suggestion column shows plain muted "Not enough data" text (explicitly
   *not* the badge component for this row-level context — see `StockRow`
   above), and P/L dashes since `position` is null.
2. **Page subtitle**: confirmed — `{stocks.length}-stock watchlist` (real
   count, derived display) + the static "stocks needing attention are
   sorted to the top" copy (describes the real server-driven order, not
   fabricated data).
3. **No-positions detection**: confirmed — `summary === null` is the
   signal, per the contract, full stop. Not scanning `stocks[].position`,
   since that would be the UI re-deriving a state the backend already
   decided — exactly what "compute nothing" prohibits.

## Implementation notes (deviations / additions beyond the plan)

- **Manual check caveat, two states not re-verified live**:
  - **No-positions**: `{data.summary && <SummaryStrip .../>}` wasn't
    exercised against a real "no trades" backend response. Making the real
    watchlist trade-less to test this would mean deleting/altering your
    actual `trades` table data, which isn't reversible the way the
    `daily_prices` trim-and-refresh trick was (refresh re-derives prices
    from yfinance; trades are your own recorded data, not re-derivable) —
    too risky for a visual check. Confidence instead comes from this being
    the exact same conditional-render pattern as 5a's
    `{data.position && <PositionCard/>}`, which *was* verified live with a
    real position present; the absent-branch behavior (render nothing) is
    the same code shape either way.
  - **Error state**: attempted the same "stop the backend, reload, restore"
    trick used for the detail page's error state in 5a, but port 8000 turned
    out to have a second listener already: your own PyCharm debug run
    (`pydevd`, separate from the `poetry run uvicorn` instance I'd started
    for testing). Stopping mine wouldn't have produced an error state since
    your PyCharm session would keep serving requests, and stopping yours
    wasn't something I was going to do. Confidence instead comes from
    `DashboardPage`'s error branch being byte-for-byte the same
    `{error && <p className="...text-bad">{error.message}</p>}` shape
    already confirmed working in 5a (verified there via a direct in-page
    `fetch()` call reproducing the exact `{error: "..."}` 404 body
    `request()` unwraps into a thrown `Error`).
- Everything else (default state with summary + real positions/warnings/
  suggestions, an insufficient-history row sorted to the bottom with its
  real price/change rendered and muted "Not enough data" text, row-click
  navigation to the correct `/stocks/{ticker}`, loading) was observed live
  against the real 13-ticker watchlist, including a repeat of the
  trim-QCOM's-`daily_prices`-then-`POST /api/refresh`-to-restore trick from
  5a to exercise the insufficient-history row (confirmed back to 42 rows
  afterward).
