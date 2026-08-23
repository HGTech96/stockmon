# Phase 10c — Dashboard refresh button

## Overview

Add a "Refresh now" button directly above the dashboard stock table. On click
it calls the existing `POST /api/refresh`, then invalidates the dashboard
queries so the table, money strip, and freshness timestamp update. UI-only —
no backend or contract change; `POST /api/refresh` and its response shape
(`refreshed`/`failed`/`dataAsOf`) already exist and are unchanged.

**No refresh button exists today.** Phase 6's "Auto-refetch interval" item
added `useDataRefresh.js` (a 15-min `setInterval` that calls `postRefresh()`
and blindly does `queryClient.invalidateQueries()` with no key, discarding
the response) but never added a user-facing button — that plan checkbox is
still unchecked. There is nothing to move; this is a net-new component. The
old interval hook stays as-is (out of scope for 10c).

## Files to create/change

```
ui/src/
├── pages/dashboard/
│   ├── DashboardPage.jsx      (change: render RefreshButton above StockTable)
│   └── RefreshButton.jsx      (new: button + mutation + inline failure notice)
└── lib/
    └── format.js              (change: add fmtRefreshSummary helper)
```

No changes to `ui/src/api/refresh.js` or `ui/src/api/types.js` — `postRefresh()`
and the `RefreshResponse` typedef already match the contract exactly.

## Behavior

- Button sits in the header row of `DashboardPage.jsx` (same row as the "N
  stocks" line, `justify-between`), directly above `<StockTable/>`.
- Click → `useMutation(postRefresh)`.
  - Pending: button `disabled`, label swaps to `"Refreshing…"` — same
    label-swap-and-dim pattern used everywhere else in the app (e.g.
    `TradeModal`'s `"Saving…"`); no spinner icon exists anywhere in this
    codebase, so none is introduced here.
  - Success: invalidate `["stocks"]`, `["portfolio"]`, `["cash"]` — the same
    triple already used by `TradeModal`/`EditTradeModal`/`DeleteTradeConfirm`
    after a mutation (`["cash"]` is currently a no-op key, kept for
    consistency with `CashModal`'s existing defensive invalidation).
  - If `response.failed.length > 0`: show an inline notice below the button,
    styled with the same warn-token triad as `TradeModal`'s 422 error box
    (`border-warn-border bg-warn-bg text-warn`) — names the failed tickers,
    e.g. "5 updated · AMZN, KO failed" (not just a count — per-ticker
    `error` text from the contract is more detail than needed inline, but
    the ticker symbols themselves must be visible so a stale price is
    identifiable at a glance). No notice when `failed` is empty; the
    freshness timestamp updating is sufficient (per CLAUDE.md honesty
    principle — no toast for silent success, but no silent failure either).
  - Mutation errors (network failure, non-2xx) are unlikely for this
    endpoint per contract (partial failure is still `200`) but are handled
    the same way `request()` already throws elsewhere: show the thrown
    message in the same warn box.

## Schemas / interfaces

No new types — reuses existing:

```js
// ui/src/api/types.js (existing, unchanged)
/** @typedef {{ ticker: string, error: string }} RefreshFailure */
/** @typedef {{ refreshed: string[], failed: RefreshFailure[], dataAsOf: string }} RefreshResponse */
```

New formatting helper (`ui/src/lib/format.js`), following the file's existing
one-function-per-concern style:

```js
/**
 * @param {import('../api/types').RefreshResponse} refreshResult
 * @returns {string|null} e.g. "5 updated · AMZN, KO failed" — null when nothing failed
 */
export function fmtRefreshSummary(refreshResult) { ... }
```

## Task list

- [x] Add `fmtRefreshSummary(refreshResult)` to `ui/src/lib/format.js`
      (returns `null` when `failed.length === 0`, otherwise
      "N updated · TICKER, TICKER failed" naming the failed tickers)
- [x] Create `ui/src/pages/dashboard/RefreshButton.jsx`:
  - [x] `useMutation` wrapping `postRefresh`
  - [x] button: matches existing raw-`<button>` styling (`TradeModal`'s
        primary button classes — the established raw-Tailwind convention,
        not the shadcn `Button` primitive, which is known tech debt flagged
        in Phase 8 and shouldn't be spread further), disabled +
        `"Refreshing…"` label while `mutation.isPending`
  - [x] on success: invalidate `["stocks"]`, `["portfolio"]`, `["cash"]`
  - [x] inline warn-toned notice rendered when `fmtRefreshSummary` returns
        non-null, or when `mutation.isError`
- [x] Wire `<RefreshButton/>` into `DashboardPage.jsx`, directly above
      `<StockTable/>` (its own right-aligned row, rather than the top
      header row, so it reads as scoped to the table it refreshes)
- [x] Manual test: clicked with dev server + real yfinance watchlist —
      confirmed disabled/dimmed button with "Refreshing…" label during the
      request (screenshot), and `POST /api/refresh` followed by an
      auto-refetched `GET /api/stocks` (network log) with the freshness
      timestamp advancing after. All tickers succeeded in this run, so no
      failure notice was exercised live — reviewed by code inspection
      instead (`fmtRefreshSummary` unit-level logic is straightforward
      string building, no test framework wired up for `ui/src/lib` in this
      repo).
- [x] Check off Phase 10c in `docs/plan.md`

## Open questions

None — styling precedent (`TradeModal` raw Tailwind, not the shadcn `Button`
primitive) and failure-notice format (name the failed tickers, not just a
count) both confirmed in review.
