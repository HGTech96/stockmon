# Phase 5c — Portfolio Page + Trade Modal

## Overview

Build the real Portfolio page (`/portfolio`) from `GET /api/portfolio`, and
the Add/Edit Trade modal that both its states open, per
`design/reference/.../dashboard-src.html`'s `#page-portfolio` and
`#modal-overlay`. This is the last Phase 5 item — after this, every page
renders real data instead of a JSON dump.

Reuses `SummaryStrip` and `SuggestionBadge` as-is (both already shared).
`fmtToGo` (new, see below) also retrofits 5a's `PositionCard`, which had the
same "$X to go" / "Goal reached" text inlined instead of in `lib/format.js`
— a small consistency fix now that a second consumer needs the identical
logic. The modal uses shadcn's `Dialog` primitive (in the stack per
CLAUDE.md, not yet pulled in) for overlay/focus-trap/Escape-to-close
mechanics, rather than hand-rolling that; everything inside it (stock
select, segmented Buy/Sell toggle, inputs) is plain elements styled to the
reference's `.field`/`.segmented` classes, matching the reference's own
choice of plain form controls.

## Files to create/change

```
ui/src/
├── components/
│   └── ui/
│       └── dialog.jsx                    NEW — via `npx shadcn@latest add dialog`
├── lib/
│   └── format.js                         CHANGE — add fmtToGo(remainingDollars, reached)
└── pages/
    ├── stock-detail/
    │   └── PositionCard.jsx              CHANGE — use fmtToGo instead of its inline ternary
    └── portfolio/
        ├── PortfolioPage.jsx             REWRITE
        ├── PositionsTable.jsx            NEW — table shell + header row
        ├── PositionRow.jsx               NEW — one clickable row
        ├── EmptyState.jsx                NEW — no-trades empty state + Add trade button
        └── TradeModal.jsx                NEW — add-trade dialog
```

`api/trades.js` (`postTrade`) and `api/portfolio.js` (`getPortfolio`) already
exist from Phase 4 and need no changes.

## Schemas / interfaces

**`lib/format.js`** — one addition:
```js
export function fmtToGo(remainingDollars, reached)
  // reached -> "Goal reached"; else -> "$X to go" (fmtMoney(remainingDollars) + " to go")
```

**`pages/portfolio/PositionRow.jsx`**
```jsx
/**
 * @param {{ position: import('../../api/types').PortfolioPosition }} props
 * One clickable row (click / Enter / Space -> `/stocks/{ticker}`, same
 * pattern as Dashboard's StockRow). Columns: stock id, shares, avg cost,
 * invested, current value, P/L ($ + % colored), to-target (fmtToGo), and
 * Suggestion. Suggestion column follows the exact convention 5b established
 * for Dashboard: `<SuggestionBadge label={position.suggestion} size="sm"/>`
 * when `status === "ok"`, plain muted "Not enough data" text (no badge
 * chrome) when `status === "insufficient_history"`.
 */
export function PositionRow({ position }) { ... }
```

**`pages/portfolio/PositionsTable.jsx`**
```jsx
/**
 * @param {{ positions: import('../../api/types').PortfolioPosition[] }} props
 * Table shell (Stock / Shares / Avg cost / Invested / Current value / P/L /
 * To target / Suggestion header row) + one <PositionRow/> per entry, in
 * array order (positions with `sharesHeld` reduced to 0 are already
 * excluded server-side per contract -- no client filtering here).
 */
export function PositionsTable({ positions }) { ... }
```

**`pages/portfolio/EmptyState.jsx`**
```jsx
/**
 * @param {{ onAddTrade: () => void }} props
 * No-trades state per the reference: inbox icon, "No trades recorded yet"
 * heading, explanatory copy, "Add trade" button wired to open the modal.
 */
export function EmptyState({ onAddTrade }) { ... }
```

**`pages/portfolio/TradeModal.jsx`**
```jsx
/**
 * @param {{
 *   open: boolean, onClose: () => void,
 *   watchlist: string[],
 *   stocksByTicker: Map<string, {companyName, currentPrice}>,
 *     // built from the `["stocks"]` query result (see decision #1 below);
 *     // empty map is a valid state -- dropdown just falls back to bare
 *     // ticker labels and no price prefill.
 *   ownedTickers: Set<string>, // from portfolio.positions, for the hint
 * }} props
 *
 * shadcn <Dialog>. Fields: stock <select> (watchlist tickers, label
 * "TICKER · Company name" when stocksByTicker has the name, else bare
 * ticker), Buy/Sell segmented toggle (defaults Buy), shares (number,
 * min 0.01, required), price per share (number, min 0.01, required,
 * prefilled from stocksByTicker on stock selection, still editable), date
 * (defaults to today, HTML date input -- browser enforces a real calendar
 * value, no future-date check client-side since the backend owns that
 * rule). Hint line ("This will update your average purchase price for
 * this stock.") shows only when side is Buy AND the selected ticker is in
 * ownedTickers.
 *
 * Submit runs `useMutation(postTrade)`: pending -> fields + submit button
 * disabled, button reads "Saving…", AND the dialog itself becomes
 * non-dismissible (Escape / backdrop click / close-X all no-op while
 * pending) so a slow request never reads as a silent failure or lets the
 * user close over an in-flight submit; error -> the 422 body's `error`
 * message rendered inline in the modal (dialog re-becomes dismissible,
 * form stays open, values kept so the user can correct and resubmit);
 * success -> `onClose()`, then invalidate both `["stocks"]` and
 * `["portfolio"]` query keys so Dashboard and Portfolio both refetch and
 * reflect `updatedPosition` on next render. No toast -- the modal closing
 * plus the table showing the new numbers is the confirmation.
 *
 * Client-side validation is required + positive-number only (shares > 0,
 * price > 0, stock chosen) via native `required`/`min` input attributes --
 * everything else (sell exceeds held shares, sell of no position, future
 * date, ticker not on watchlist) is the backend's 422, never duplicated
 * here.
 */
export function TradeModal({ open, onClose, watchlist, stocksByTicker, ownedTickers }) { ... }
```

**`PortfolioPage.jsx`** — composition:
- loading / error: same centered-text pattern as Dashboard/StockDetail
- also runs `useQuery(["stocks"], getStocks)` alongside its own
  `useQuery(["portfolio"], getPortfolio)` -- see decision #1
- header: "Portfolio" + `{positions.length} position{s}` (matches the
  reference's pluralization) when `hasTrades`, else the reference's
  "Your recorded positions" default sub-copy
- `hasTrades === false` (equivalently `summary === null`, per contract):
  `<EmptyState onAddTrade={...} />`, no summary strip, no table
- `hasTrades === true`: `<SummaryStrip summary={data.summary} />`, an
  "Add trade" button above the table, `<PositionsTable positions={data.positions} />`
- `<TradeModal>` always mounted, `open` state lifted in this page, opened by
  either "Add trade" button

## Task list

- [x] `npx shadcn@latest add dialog` (generates `components/ui/dialog.jsx`)
- [x] `lib/format.js`: add `fmtToGo`
- [x] Retrofit `pages/stock-detail/PositionCard.jsx` to use `fmtToGo`
- [x] `pages/portfolio/PositionRow.jsx`
- [x] `pages/portfolio/PositionsTable.jsx`
- [x] `pages/portfolio/EmptyState.jsx`
- [x] `pages/portfolio/TradeModal.jsx`
- [x] Rewrite `pages/portfolio/PortfolioPage.jsx`
- [x] Manual check via `claude-in-chrome` against the real backend: positions state (summary + table + to-target text), row click navigates to detail, modal open/close, Escape-to-close, stock selection prefills price + shows/hides the hint correctly for owned vs. sell side, a validation error (selling more shares than held) exercising the inline error state, a real buy+sell trade pair exercising success and the close-position path — see implementation notes for the trade details and the one state not re-verified live
- [x] Check off "Portfolio page" and "Add/Edit trade modal" under Phase 5 in `docs/plan.md`

## Decisions from review

1. **Shared `["stocks"]` query, approved as the correct design** (not a
   workaround): same query key is the app's single cache entry for that
   data, which is exactly what TanStack Query is for. Blank-form fallback
   rejected as worse UX for no architectural benefit.
2. **No toast, confirmed** — with one added requirement: the dialog must be
   non-dismissible while the mutation is pending (see `TradeModal` above),
   so a slow request never looks like a silent failure. Failure keeps the
   modal open with the server's message; success = close + refetched table,
   which is confirmation enough for a single-user app.
3. **Real buy+sell trade pair, approved**, framed as a feature not a
   compromise: it's the only check so far that exercises the close-position
   path (`updatedPosition: null`) through the real UI. Conditions:
   - Before: capture the real baseline (current position state / summary
     totals) via `GET /api/portfolio` so the after-state can be diffed
     against something concrete, not assumed.
   - Report the exact ticker, shares, and price of both the buy and the
     sell in the final summary so you can verify the pair nets out.
   - After the sell-back: re-check `GET /api/portfolio` and confirm the
     position is fully closed (`updatedPosition: null` from the sell
     response, ticker absent from `positions[]` afterward) and that
     `summary` totals match the pre-test baseline.

## Implementation notes (deviations / additions beyond the plan)

- **`mutation.reset()` added on ticker/side change**, not called out in the
  plan. Found live: after the deliberate validation-error test (selling 999
  AAPL shares), switching the stock dropdown to a different, valid ticker
  left the old error message on screen even though the form was now valid —
  confusing since it referenced a ticker no longer selected. Both
  `TradeModal`'s ticker-select and Buy/Sell-toggle handlers now call
  `mutation.reset()` so a stale error never survives past the field that
  would invalidate it. (It still doesn't clear on shares/price edits, which
  is fine — an error tied to "sell exceeds held shares" stays relevant
  until you change shares or resubmit, at which point the resubmit itself
  replaces it.)
- **Real trade pair executed and verified, per your conditions:**
  - Baseline (`GET /api/portfolio` before any test trade): 1 position
    (AAPL, 10 shares @ $185.25 avg), `summary`: invested $1,852.50, current
    value $3,168.30, P/L +$1,315.80 (+71.03%).
  - **Buy: 1 share of RKLB @ $75.84, dated 2026-08-20** (today, via the
    modal's own default) — submitted through the real UI. Modal closed,
    Dashboard/Portfolio queries invalidated, Portfolio table immediately
    showed the new RKLB row (1 share, $75.84 invested/current value, +$0.00
    P/L, "$50.00 to go") and "2 positions" in the header.
  - **Sell: 1 share of RKLB @ $75.84, dated 2026-08-20** — submitted the
    same way. Modal closed, RKLB row disappeared, header returned to
    "1 position".
  - Verified via a direct `GET /api/portfolio` call after the sell: response
    byte-for-byte identical to the pre-test baseline above — `positions`
    contains only AAPL (RKLB absent, confirming the sell fully closed it
    server-side, i.e. `updatedPosition: null` took effect), and `summary`
    totals match exactly.
  - Along the way, also verified the validation-error state live: selling
    999 AAPL shares (999 > the 10 held) surfaced the backend's real 422
    message inline in the modal ("Cannot sell 999 shares of AAPL; only
    10.0000 held"), form stayed open with values intact, no data was
    written.
- **Manual check caveat, one state not re-verified live**: the empty state
  (`hasTrades === false`) wasn't exercised against a real trade-less
  backend response, for the same reason noted in 5b — doing so would mean
  deleting your actual `trades` table rows, which (unlike the `daily_prices`
  trim-and-refresh trick) isn't reversible from re-fetchable external data.
  Confidence comes from `{data.hasTrades ? <positions view> : <EmptyState/>}`
  being the same conditional-render shape as 5b's already-verified
  `{data.summary && <SummaryStrip/>}`, and from `EmptyState` itself being a
  simple, static-content component with no data-dependent branches to get
  wrong.
- Loading and error (bad-request/unreachable-backend) states use the same
  already-verified pattern from 5a/5b (`{isPending ...}` / `{error ...}`
  centered text) — not re-screenshotted separately this session, consistent
  with how 5b treated its own already-proven patterns.
