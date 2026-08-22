# Phase 9d — Wire the cash model to real data

## Overview

Takes the approved 9b/9c `MoneyStrip` design off the `/preview/cash` mock
and wires it to the live `money` block (contract v1.5) on `GET /api/stocks`
and `GET /api/portfolio`. Adds a Deposit/Withdraw flow (`POST /api/cash`)
behind the strip's existing `+`/`−` buttons, surfaces insufficient-cash
errors inline, and removes the temporary preview route. No backend changes
— 9a already shipped the endpoints and `money` fields; this phase is UI-only.

The buy-flow 422 ("Insufficient cash — record a deposit first.") already
renders through `TradeModal`'s existing generic error box (it just shows
`mutation.error.message` verbatim) — no code change expected there, just
verification.

**Fresh-DB bootstrap (resolved, see open questions below):** `money` is
`null` until any cash activity or trade exists — which is the actual
starting state of this app (a truncated DB, not a hypothetical edge case).
Without an entry point in that state, there's no way to make the first
deposit through the UI at all. So a minimal `EmptyMoneyStrip` (just a Cash
label, "$0.00", and a Deposit button — no Withdraw, no Realized/Unrealized)
renders whenever `money` is `null`, closing the loop into the real
`MoneyStrip` once the first deposit lands.

## Files to create/change

```
ui/src/
  api/
    cash.js                      (new — postCashEvent)
    types.js                     (change — add `money` to DashboardResponse
                                   and PortfolioResponse; add CashEvent,
                                   CashEventRequest, CashEventResponse)
  components/
    money/
      MoneyStrip.jsx              (change — accept onDeposit/onWithdraw,
                                   wire to the two icon buttons)
      EmptyMoneyStrip.jsx         (new — single-cluster "Cash: $0.00" +
                                   Deposit-only bar, shown when
                                   `money` is null)
      CashModal.jsx               (new — deposit/withdraw form dialog,
                                   same modal convention as TradeModal)
  pages/
    dashboard/
      DashboardPage.jsx           (change — render MoneyStrip or
                                   EmptyMoneyStrip + CashModal, always —
                                   money is either present or bootstrapped)
    portfolio/
      PortfolioPage.jsx           (change — same, pulled above the
                                   hasTrades empty-state branch)
    preview/
      CashPreviewPage.jsx         (delete)
  App.jsx                         (change — remove /preview/cash route)
docs/planning/phase-9d-finalize.md (this file)
```

## Schemas / interfaces

```js
// api/types.js — additions

/**
 * @typedef {Object} DashboardResponse
 * @property {Meta} meta
 * @property {Summary|null} summary
 * @property {Money|null} money
 * @property {DashboardStock[]} stocks
 */

/**
 * @typedef {Object} PortfolioResponse
 * @property {Meta} meta
 * @property {boolean} hasTrades
 * @property {Summary|null} summary
 * @property {Money|null} money
 * @property {PortfolioPosition[]} positions
 * @property {string[]} watchlist
 */

/**
 * @typedef {Object} CashEventRequest
 * @property {"deposit"|"withdraw"} type
 * @property {number} amountUsd
 * @property {string} date - YYYY-MM-DD
 */

/**
 * @typedef {Object} CashEvent
 * @property {number} id
 * @property {"deposit"|"withdraw"} type
 * @property {number} amountUsd
 * @property {string} date
 */

/**
 * @typedef {Object} CashEventResponse
 * @property {CashEvent} event
 * @property {number} cashAvailable
 */
```

```js
// api/cash.js
import { request } from "./client";

/**
 * @param {import('./types').CashEventRequest} payload
 * @returns {Promise<import('./types').CashEventResponse>}
 */
export function postCashEvent(payload) {
  return request("/cash", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
```

```
MoneyStrip({ money, onDeposit, onWithdraw })
  // onDeposit/onWithdraw: () => void, called by the existing +/- icon
  // buttons (currently inert). No other prop changes.

EmptyMoneyStrip({ onDeposit })
  // Rendered instead of MoneyStrip when `money` is null. One row, same
  // card language (rounded-DEFAULT border border-border bg-surface) but
  // a single "Cash" cluster: label + "$0.00" + a lone Deposit (+) button.
  // No Withdraw button -- nothing to withdraw before the first deposit.

CashModal({ type, cashAvailable, onClose })
  // type: "deposit" | "withdraw" | null — null means closed (same
  // "open = value != null" convention as EditTradeModal's `trade` prop).
  // cashAvailable: number, for the withdraw-only "Available: $X" caption
  // (undefined/omitted when opened from EmptyMoneyStrip, always "deposit").
  // Owns its own useMutation(postCashEvent) + useQueryClient
  // invalidation, same pattern as TradeModal/EditTradeModal.
```

## Task list

- [x] `api/cash.js` — `postCashEvent`
- [x] `api/types.js` — add `money` to `DashboardResponse`/`PortfolioResponse`;
      add `CashEvent`, `CashEventRequest`, `CashEventResponse`
- [x] `CashModal.jsx` — amount + date fields (same field styling as
      TradeModal/EditTradeModal), title "Deposit cash" / "Withdraw cash"
      from `type`; Withdraw form shows a small "Available: $X" caption
      from the already-fetched `cashAvailable` prop (display only, no
      client-side blocking — the 422 stays as the backstop); on success
      invalidate `["stocks"]`, `["portfolio"]`, `["cash"]`; 422 message
      rendered inline in the same warn-box pattern as TradeModal; can't be
      dismissed while submitting
- [x] `MoneyStrip.jsx` — wire the two icon buttons to `onDeposit`/`onWithdraw`
      props instead of being inert
- [x] `EmptyMoneyStrip.jsx` — single "Cash" cluster (reuses `MoneyCluster`
      + `MoneyTile` with one tile, "$0.00", `actions` = just the Deposit
      button) for when `money` is null; no Withdraw button
- [x] `DashboardPage.jsx` — render `<MoneyStrip money={data.money} .../>`
      when `data.money` exists, else `<EmptyMoneyStrip/>` — the cash block
      always renders, independent of `data.summary`; local `cashModalType`
      state + `<CashModal/>`, mirroring how `PortfolioPage` already owns
      `TradeModal`'s open state
- [x] `PortfolioPage.jsx` — pull `SummaryStrip`/money-block rendering out
      of the `hasTrades` branch: `summary` and the "Add trade" button /
      `PositionsTable` stay conditional on `hasTrades`, but `MoneyStrip`/
      `EmptyMoneyStrip` always renders (money-or-empty, same rule as
      Dashboard) above the `hasTrades ? ... : <EmptyState/>` branch; same
      `cashModalType` + `<CashModal/>` wiring as Dashboard
- [x] Delete `pages/preview/CashPreviewPage.jsx` and its route in `App.jsx`
- [x] Manual verification in the browser end to end (see below)

## Manual verification

- [x] Fresh/current DB (`money` null): `EmptyMoneyStrip` renders on both
      Dashboard and Portfolio, Deposit button opens `CashModal`
- [x] First deposit $X from `EmptyMoneyStrip` → `money` becomes non-null on
      next fetch, `MoneyStrip` (all three clusters) replaces
      `EmptyMoneyStrip`, `cashAvailable` and `netDeposited` both read $X
- [x] Withdraw form shows "Available: $X" matching the fetched
      `cashAvailable`
- [x] Deposit further $X: dashboard and portfolio `cashAvailable`
      rise by $X, `netDeposited` rises by $X, both queries refetch without
      a manual reload
- [x] Buy within cash → `cashAvailable` falls, `netDeposited` unchanged
- [x] Buy exceeding cash → 422 "Insufficient cash — record a deposit
      first." shown inline in the existing trade-modal error box
- [x] Sell → `cashAvailable` rises by proceeds, `realizedEarned`/
      `realizedLost` and `unrealizedGainOpen`/`unrealizedLossOpen` update,
      `netDeposited` stays flat (proves recycling, not double-counting)
- [x] Withdraw within cash → `cashAvailable` falls, `netDeposited` falls
- [x] Withdraw exceeding cash → 422 "Can't withdraw more than your
      available cash." shown inline in `CashModal`
- [x] `/preview/cash` route removed — no route matches, no leftover
      references in App.jsx or the filesystem (SPA renders blank rather
      than a server 404, as expected for client-side routing)
- [x] Console clean, no stray network errors, across both pages

## Decisions from review

1. **Bootstrapping the first deposit: option (b).** Fresh DB is the app's
   normal starting state, not an edge case — `EmptyMoneyStrip` gives it a
   Deposit entry point so the UI is never a dead end. See "Fresh-DB
   bootstrap" note above and the `EmptyMoneyStrip` component.
2. **"Available: $X" caption: kept.** Display-only, zero cost (data's
   already fetched), and prevents the 422 rather than just explaining it
   after the fact — consistent with the app's show-the-reasoning
   principle. The 422 remains the authoritative backstop.
