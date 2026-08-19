# Phase 5a — Stock Detail Page

## Overview

Build the real Stock Detail page (`/stocks/:ticker`), replacing the Phase 4
JSON-dump placeholder. Matches `design/reference/.../dashboard-src.html`'s
`#page-detail` layout exactly (colors/spacing/radii/shadows already live as
Tailwind theme tokens from Phase 4 — no new hex values). Renders only what
`GET /api/stocks/{ticker}` sends; no client-side calculations.

Two components are built reusable now per your instruction, since Dashboard
and Portfolio will need them next session: `SuggestionBadge` (small badge for
table rows, large for the detail header) and `SuggestionChecklist` (the
"Why · N of M conditions met" box). Chart uses Recharts (already in the
stack per CLAUDE.md, not yet an installed dependency — added this session).

## Files to create/change

```
ui/
├── package.json                              CHANGE — add recharts
└── src/
    ├── lib/
    │   └── format.js                         CHANGE — real formatters (was a placeholder)
    ├── components/
    │   ├── layout/
    │   │   └── FreshnessBar.jsx              CHANGE — real fmtTimestamp text; new `showDot` prop
    │   │                                     so DetailHeader can reuse it dot-less (one component,
    │   │                                     two placements — see decisions below)
    │   ├── badge/
    │   │   └── SuggestionBadge.jsx           NEW — shared (dashboard/portfolio reuse later)
    │   ├── checklist/
    │   │   └── SuggestionChecklist.jsx       NEW — shared
    │   └── charts/
    │       └── PriceVolumeChart.jsx          NEW — shared
    └── pages/stock-detail/
        ├── StockDetailPage.jsx               REWRITE — composes everything below
        ├── DetailHeader.jsx                  NEW — ticker/name/price/trend/badge/timestamp
        ├── WarningBanner.jsx                 NEW — sharp-move banner
        ├── InsufficientHistoryPanel.jsx      NEW
        ├── IndicatorsPanel.jsx               NEW — two-column indicator grid
        ├── PositionCard.jsx                  NEW — position grid + target progress bar
        └── NewsLinksPanel.jsx                NEW
```

## Schemas / interfaces

**`lib/format.js`** — every formatter the design reference has, ported
1:1 (`design/reference/.../app-src.js` `fmt*` functions), operating on the
contract's raw numbers/ISO strings. No component formats inline.

```js
export function fmtMoney(n)        // "$1,234.56" (unsigned, comma grouped)
export function fmtMoneySigned(n)  // "+$111.20" / "-$45.00"
export function fmtPct(n)          // "+6.30%" / "-1.20%" / "0.00%" (|n|<0.005)
export function fmtPrice(n)        // "$187.42" (no comma grouping, matches design)
export function fmtVolume(n)       // raw share count -> "55.9M" (n / 1e6)
export function fmtShares(n)       // "1,234" (comma grouped integer)
export function fmtDateShort(isoDate)   // "YYYY-MM-DD" -> "Jul 21"
export function fmtDateLong(isoDate)    // "YYYY-MM-DD" -> "Wed, Jul 21"
export function fmtTimestamp(isoDatetime) // -> "Tuesday, 2:45 PM" (contract's display convention)
export function fmtOrDash(value, formatter) // null -> "–"; else formatter(value).
  // The one place the null-numeric-to-dash convention lives, so it's the
  // same character/behavior everywhere a nullable contract number is
  // rendered (detail header price/change today; dashboard/portfolio reuse
  // it next session for their own "-" cells).
```

**`components/badge/SuggestionBadge.jsx`**
```jsx
/**
 * @param {{ label: "BUY"|"WAIT"|"SELL"|"INSUFFICIENT", size?: "sm"|"lg" }} props
 * label is the machine enum from `suggestion.label`; pass "INSUFFICIENT" when
 * `status === "insufficient_history"` (suggestion is null in that case — this
 * is a status-driven variant, not part of the Suggestion object).
 * Colors per CLAUDE.md: BUY=good(green), SELL=warn(orange), WAIT=neutral(gray),
 * INSUFFICIENT=sunken gray. Renders "Possible buy"/"Wait"/"Possible sell"/
 * "Not enough data" text, uppercased via CSS.
 */
export function SuggestionBadge({ label, size = "sm" }) { ... }
```

**`components/checklist/SuggestionChecklist.jsx`**
```jsx
/**
 * @param {{ suggestion: import('../../api/types').Suggestion }} props
 * Renders "Why · {metCount} of {totalCount} conditions met", the pass/fail
 * list (check/cross icon per item.passed, item.text verbatim from backend),
 * and `note` when non-null. Per CLAUDE.md, a badge is never rendered without
 * this nearby -- pages compose the two together, this component never
 * renders a badge itself.
 */
export function SuggestionChecklist({ suggestion }) { ... }
```

**`components/charts/PriceVolumeChart.jsx`**
```jsx
/**
 * @param {{ chart: import('../../api/types').ChartData }} props
 * Recharts ComposedChart, single shared x-axis (chart.days, oldest first):
 *  - Line: close price (left y-axis)
 *  - Bar: volume (right y-axis, domain padded so bars occupy the bottom band
 *    only, matching the reference's stacked price/volume panes); today's bar
 *    highlighted in accent color, others border-strong
 *  - ReferenceLine (dashed, ink-faint): chart.thirtyDayAverage
 *  - ReferenceLine (dashed, accent): chart.userAvgPurchasePrice, only when non-null
 *  - Custom tooltip: date (long) + close (fmtPrice) + volume (fmtVolume), one
 *    row's data since days[] is the single shared array per contract
 *  - Legend row above chart: Price / 30-day average / Your average cost (conditional)
 */
export function PriceVolumeChart({ chart }) { ... }
```

**`pages/stock-detail/*.jsx`** (page-specific, not reused elsewhere yet)
```jsx
/** @param {{ ticker, companyName, currentPrice, change1dPct, status, suggestion, meta }} props
 * Ticker + company name, price + 1d trend (both via fmtOrDash — "–" when
 * null, row structure unchanged so nothing jumps), SuggestionBadge (lg),
 * and <FreshnessBar meta={meta} showDot={false} /> for the timestamp line
 * — deliberate redundancy with the app-shell's freshness bar: a screenshot
 * of this page alone must still carry its own data timestamp. */
export function DetailHeader(props) { ... }

/** @param {{ warning: import('../../api/types').Warning }} props
 * Orange banner rendering warning.text verbatim, styled per the reference
 * (icon + single line, above the checklist). No client-built second
 * sentence from ticker/change1dPct — if a richer banner is ever wanted,
 * the backend's `text` changes, not this component. Returns null if
 * warning is null. */
export function WarningBanner({ warning }) { ... }

/** @param {{ daysOfHistoryAvailable, daysOfHistoryRequired, tradingDaysUntilReady }} props */
export function InsufficientHistoryPanel(props) { ... }

/** @param {{ indicators: import('../../api/types').Indicators }} props
 * Two-column <dl> grid, 6 rows each, values via lib/format.js. */
export function IndicatorsPanel({ indicators }) { ... }

/** @param {{ position: import('../../api/types').Position }} props
 * Position grid (shares/avg cost/invested/current value/P&L/P&L%) +
 * profit-target progress bar from position.profitTarget
 * (progressDollars/targetDollars/remainingDollars/reached — all server-computed). */
export function PositionCard({ position }) { ... }

/** @param {{ newsLinks: import('../../api/types').NewsLinks }} props
 * Yahoo + Google links always render; investorRelations link only when non-null
 * (never fabricate a search-link fallback the way the design mock does). */
export function NewsLinksPanel({ newsLinks }) { ... }
```

**`StockDetailPage.jsx`** — composition, no new business logic:
- loading: centered "Loading…" text
- error (incl. 404 unknown ticker): centered error message from the thrown `Error`
- "Back to dashboard" link (`react-router-dom` `Link` to `/`)
- `status === "insufficient_history"`: header + InsufficientHistoryPanel + NewsLinksPanel (no chart/indicators, per contract)
- `status === "ok"`: header + WarningBanner (if any) + SuggestionChecklist, then a two-column body: main column (PriceVolumeChart panel, IndicatorsPanel), side column (PositionCard when `position` non-null, then NewsLinksPanel)

## Task list

- [x] Add `recharts` to `ui/package.json`, `npm install`
- [x] `lib/format.js`: implement all formatters listed above
- [x] `FreshnessBar.jsx`: swap placeholder formatter for `fmtTimestamp`
- [x] `components/badge/SuggestionBadge.jsx`
- [x] `components/checklist/SuggestionChecklist.jsx`
- [x] `components/charts/PriceVolumeChart.jsx`
- [x] `pages/stock-detail/DetailHeader.jsx`
- [x] `pages/stock-detail/WarningBanner.jsx`
- [x] `pages/stock-detail/InsufficientHistoryPanel.jsx`
- [x] `pages/stock-detail/IndicatorsPanel.jsx`
- [x] `pages/stock-detail/PositionCard.jsx`
- [x] `pages/stock-detail/NewsLinksPanel.jsx`
- [x] Rewrite `pages/stock-detail/StockDetailPage.jsx` composing all of the above, covering every state
- [x] Manual check via `claude-in-chrome` against the real backend: ok+owned, ok+not-owned, warning banner active, insufficient history, loading, error (bad ticker) — confirm badge+checklist always paired, position card/avg-cost line appear only when owned, stale banner still works globally
- [x] Check off "Stock detail page" under Phase 5 in `docs/plan.md`

## Decisions from review

1. **Warning banner**: single line, `warning.text` verbatim, styled per the
   reference banner (orange, above the checklist). No client-composed second
   sentence from ticker/`change1dPct` — the design mock's two-line version
   violated "render what the API sends."
2. **Detail header timestamp**: kept, as deliberate redundancy with the
   app-shell's freshness bar (a lone screenshot of the detail page must still
   carry its own timestamp). Implemented as one component, two placements —
   `FreshnessBar` gains a `showDot` prop; `AppShell` keeps `showDot={true}`
   (default), `DetailHeader` renders it with `showDot={false}`. No separate
   timestamp-formatting logic duplicated in `DetailHeader`.
3. **Null numeric → dash**: confirmed, row structure stays fixed so layout
   doesn't jump. Generalized as `fmtOrDash(value, formatter)` in
   `lib/format.js` (see above) rather than a one-off in `DetailHeader`, so
   the same convention is available app-wide when Dashboard/Portfolio need
   it next session.

## Implementation notes (deviations / additions beyond the plan)

- **Added `components/panel/Panel.jsx`** (not in the original file tree): a
  shared `.panel`-equivalent card shell (title + optional subtitle + border/
  shadow chrome). Without it, `PositionCard`/`NewsLinksPanel` would each
  reimplement the same card chrome while `IndicatorsPanel`/`PriceVolumeChart`
  had none — `Panel` wraps all four consistently from `StockDetailPage`, and
  those four components now render pure content only. Reusable for
  Portfolio's panels next session too.
- **Added `fmtRounded(n)`** to `lib/format.js`, not in the original formatter
  list. Found live: the real backend's `indicators.rsi` is an unrounded
  float (e.g. `55.46222647532291`), unlike the design mock's pre-rounded
  fake data. `IndicatorsPanel` uses it for the "RSI (14-day)" row; the
  checklist's RSI wording is unaffected since that text string comes
  pre-formatted from the backend.
- **`StockDetailPage`'s "Back to dashboard" link** lives inline in the page
  file (a `BackLink` sub-component) rather than as its own file — it's a
  three-line `react-router-dom` `Link`, not a reusable piece, and the plan's
  file tree didn't call out a separate component for it.
- **Manual check caveat**: verified via `claude-in-chrome` against the real
  backend (13 real watchlist tickers): AAPL (owned, WAIT via exit checklist,
  profit target reached → "Goal reached" progress bar, dashed avg-cost
  line), AVGO (not owned, BUY, warning banner active, no position
  card/avg-cost line, exactly per contract). Insufficient-history has no
  naturally occurring ticker in the seeded watchlist, so QCOM's
  `daily_prices` rows were temporarily trimmed from 42 to 12 directly in
  Postgres to exercise that state, screenshotted, then restored via
  `POST /api/refresh` (confirmed back to 42 rows afterward) — reversible,
  no trade/position data touched. The error state (bad ticker) hit the same
  test-harness artifact documented in the Phase 4 plan: an automated tab
  without real OS focus (`document.visibilityState: "hidden"`) pauses
  TanStack Query's retry, so the error UI couldn't be observed rendering
  live. Verified instead by calling `fetch('/api/stocks/ZZZZ')` directly in
  the page context — confirmed `404` + `{"error": "'ZZZZ' is not on the
  watchlist"}`, which is exactly the shape `request()` unwraps into a
  thrown `Error`, matching the already-verified error JSX. Loading state
  was observed directly (the "Loading…" text with the back-link, before the
  focus-pause kicked in).
