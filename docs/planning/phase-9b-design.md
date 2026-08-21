# Phase 9b — Money Block Design (static mockup, no wiring)

## Overview

Design-only. Adds the six new money figures (`money` block from contract
v1.5) to the dashboard/portfolio summary area as a **new strip below the
existing 3-card `SummaryStrip`** — nothing existing is removed or restyled.
Real components, real Tailwind tokens, hardcoded example data, mounted on a
temporary standalone route `/preview/cash` that does **not** go through
`AppShell` (AppShell mounts `useDataRefresh`, which fires a real
`POST /api/refresh` on an interval — the preview must never trigger that).
No API calls, no query hooks, no changes to `DashboardPage`/`PortfolioPage`.

**Layout choice: a second strip, not folded into the first.** The existing
strip answers "how is my portfolio doing" in one glance (invested / current
value / P&L) — that scan must survive untouched. The money strip answers a
different question ("what can I do with my cash / how did I get here") and
is visually subordinate: same card language, smaller footprint, placed
directly under the first strip so the two read as one section without
competing for the same first glance.

**Grouping: three clusters — Cash | Realized | Unrealized — not six flat
tiles.** Six ungrouped numbers is a wall; three labeled clusters of two each
map directly to the three real questions ("what can I spend", "what did I
bank", "what's still moving") and let someone stop reading after the
cluster they care about.

**Realized vs. Unrealized differentiation.** Realized tiles use the plain
solid card style already used for P&L (green/red text, `bg-surface`) — a
closed book. The Unrealized cluster gets a small pulsing dot + "moves with
the market" caption in its header, and its value cells sit on a faint tinted
background (`good-bg`/`warn-bg`-style wash at low opacity) rather than flat
white — a lightweight "this is live" signal that doesn't invent a new color
per CLAUDE.md's fixed badge semantics (still green=gain, red=loss).

**Cash cluster carries the recycling story.** `cashAvailable` (140) is
shown large/primary; `netDeposited` (100) sits underneath as a smaller,
muted reference figure with the caption "real money put in" — the $40 gap
*is* the banked-gains-recycled story, told by juxtaposition, not by a
computed sentence (no math in the UI, per CLAUDE.md — the mockup's caption
text is static, not derived).

**Deposit / Withdraw actions live in the Cash cluster header**, top-right,
as two small outline buttons with icons — closest to the numbers they
affect, consistent with "actions live next to the data they act on"
elsewhere in the app (e.g. row actions in History).

## Files to create/change

```
ui/src/
  pages/
    preview/
      CashPreviewPage.jsx        (new — standalone page: mock data + layout,
                                   not wrapped by AppShell)
  components/
    money/
      MoneyStrip.jsx             (new — lays out the 3 clusters in a row)
      MoneyCluster.jsx           (new — cluster shell: label + optional
                                   live-indicator + optional header actions
                                   + 2 child tiles)
      MoneyTile.jsx              (new — one stat: label, value, optional
                                   sub-caption, optional tinted/live bg)
  App.jsx                        (change — add standalone route
                                   `/preview/cash`, outside <AppShell>)
docs/planning/phase-9b-design.md (this file)
```

## Schemas / mock data

No API types change. `CashPreviewPage.jsx` hardcodes objects shaped exactly
like the real contract so the components are drop-in-ready for 9d:

```js
// matches Summary (api/types.js) — reused SummaryStrip, untouched
const mockSummary = {
  totalInvested: 1250.00,
  totalCurrentValue: 1421.00,
  totalProfitLoss: 171.00,
  totalProfitLossPct: 13.68,
};

// matches MoneySchema (docs/api-contract.md v1.5) — the recycling story:
// deposited 100, cash available 140 (the extra 40 is banked gains put
// back to work), one losing trade banked too, one open winner/loser.
const mockMoney = {
  cashAvailable: 140.00,
  netDeposited: 100.00,
  realizedEarned: 40.00,
  realizedLost: 12.00,
  unrealizedGainOpen: 96.00,
  unrealizedLossOpen: 18.00,
};
```

**Component props:**

```
MoneyStrip({ money })                     // money: mockMoney shape above

MoneyCluster({ label, live, actions, children })
  // label: string ("Cash" | "Realized" | "Unrealized")
  // live: bool — renders pulsing dot + "moves with the market" caption
  // actions: optional ReactNode — Deposit/Withdraw buttons (Cash only)

MoneyTile({ label, value, sub, tone, live })
  // tone: "neutral" | "good" | "bad" — text color per CLAUDE.md semantics
  // live: bool — faint tinted background per tone
```

## Layout sketch

```
┌─ existing SummaryStrip (unchanged) ─────────────────────────────┐
│  Total invested   │  Total current value  │  Total P/L          │
└───────────────────┴────────────────────────┴─────────────────────┘

┌─ new MoneyStrip ──────────────────────────────────────────────────┐
│  CASH                  │ REALIZED (banked)  │ UNREALIZED ● live   │
│  [Deposit] [Withdraw]  │                     │ moves w/ market    │
│  ─────────────────────  ─────────────────────  ─────────────────  │
│  Cash available  $140  │ Earned      +$40.00 │ Gain (open) +$96   │
│  Net deposited   $100  │ Lost        -$12.00 │ Loss (open) -$18   │
└─────────────────────────────────────────────────────────────────┘
```

Desktop: `grid-cols-3` (mirrors `SummaryStrip`'s existing pattern — `gap-px
bg-border` hairlines between cards, `rounded-DEFAULT border border-border`
outer shell). Mobile: stacks to `grid-cols-1`, same as `SummaryStrip`.

## Tasks

- [ ] `MoneyTile.jsx` — label + value + optional sub, `tone` → text color
      (`text-good`/`text-bad`/default ink), `live` → faint tinted bg wash
- [ ] `MoneyCluster.jsx` — header row (label, optional pulsing-dot +
      caption when `live`, optional right-aligned `actions` slot), 2-col
      tile grid below
- [ ] `MoneyStrip.jsx` — 3 `MoneyCluster`s in the `grid-cols-3 gap-px
      bg-border` shell matching `SummaryStrip`; Deposit/Withdraw buttons
      (existing `Button`, `size="sm" variant="outline"`, lucide
      `ArrowDownToLine`/`ArrowUpFromLine` icons) passed into the Cash
      cluster's `actions` slot — inert (no `onClick`) in this phase
- [ ] `pages/preview/CashPreviewPage.jsx` — mock data consts, renders a
      minimal static header ("Phase 9b design preview" label, not the real
      `AppShell` nav) then existing `SummaryStrip` + new `MoneyStrip`
      stacked, inside the same `max-w-[1360px] px-7 pt-7` container the
      real pages use
- [ ] `App.jsx` — add `<Route path="preview/cash" element={<CashPreviewPage
      />} />` as a top-level route, sibling to the `<Route element={<AppShell
      />}>` block, not nested inside it
- [ ] Manual check in browser at `/preview/cash`: desktop + narrow-width
      (mobile stack), confirm no network tab activity

## Open questions

1. **Deposit/Withdraw button placement** — proposed in the Cash cluster
   header (top-right, next to the label). Alternative: a single row of
   actions above the whole `MoneyStrip`, acting on "money" generally rather
   than looking cash-specific. Proposed placement (in-cluster) reads more
   directly wired to cash to me — confirm or redirect.
2. **"Live" treatment strength** — proposed: pulsing dot + caption + faint
   tinted tile background. If that reads as too busy next to the plain
   Realized cluster, the fallback is dot + caption only, no background
   tint. Want to see both before picking? I can build the tint as a toggle-
   able prop so both are one click away in the browser.
3. **Realized "lost" and Unrealized figures when zero** — real dashboards
   will often have `realizedLost: 0` etc. Proposed: still show the tile
   (never hide a figure — consistent, predictable layout) with a plain
   `$0.00`, no color emphasis when zero. Confirm that's desired over
   hiding zero-value tiles.
