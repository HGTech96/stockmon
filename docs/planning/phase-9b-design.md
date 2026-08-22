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
MoneyStrip({ money, tintLive })           // money: mockMoney shape above;
                                           // tintLive: phase-9b-only toggle,
                                           // see resolution #2 below

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

- [x] `MoneyTile.jsx` — label + value + optional sub, `tone` → text color
      (`text-good`/`text-bad`/default ink), `live` → faint tinted bg wash,
      `flex-1` so it stretches to fill its cluster's full height
- [x] `MoneyCluster.jsx` — header row (label, optional pulsing-dot +
      caption when `live`, optional right-aligned `actions` slot), tile
      row below as `flex flex-1` (not CSS grid — see post-review fix #1)
- [x] `MoneyStrip.jsx` — 3 `MoneyCluster`s in the `grid-cols-3 gap-px
      bg-border` shell matching `SummaryStrip`; Deposit/Withdraw actions
      (existing `Button`, `size="icon-sm" variant="outline"`, plain `+`/`−`
      glyphs — see post-review fix #2) passed into the Cash cluster's
      `actions` slot — inert (no `onClick`) in this phase
- [x] `pages/preview/CashPreviewPage.jsx` — mock data consts, renders a
      minimal static header ("Phase 9b design preview" label, not the real
      `AppShell` nav) then existing `SummaryStrip` + new `MoneyStrip`
      stacked, inside the same `max-w-[1360px] px-7 pt-7` container the
      real pages use
- [x] `App.jsx` — add `<Route path="preview/cash" element={<CashPreviewPage
      />} />` as a top-level route, sibling to the `<Route element={<AppShell
      />}>` block, not nested inside it
- [x] Manual check in browser at `/preview/cash`: both live-tint states
      compared via a temporary toggle, then locked in; confirmed via
      network tab that no real `/api/*` backend call fires (only Vite
      serving frontend source modules) and the console is clean

## Resolution of open questions

1. **In-cluster placement, confirmed.** Deposit/withdraw are cash-only
   actions (a buy/sell already moves cash implicitly) — putting the buttons
   in the Cash cluster header keeps that scope legible. A row above the
   whole strip would wrongly imply the actions touch Realized/Unrealized
   too.
2. **Live treatment: dot + caption + tint, confirmed after in-browser
   comparison.** Built as a toggle on the preview page, reviewed both
   states side by side, picked tint over dot-only (reverses the prior
   lean). `MoneyStrip` now hardcodes `live` on both Unrealized tiles; the
   toggle and `tintLive` prop have been removed. Guardrail still applies:
   the pulsing dot uses Tailwind's stock `animate-pulse` (slow, ~2s,
   opacity 1→0.5→1) on the 6px dot only — never on the tile background —
   so it stays calm for a tool that's on-screen all day.
3. **Zero-value figures always render, plain and neutral, confirmed.**
   `MoneyTile` only applies `tone` color (`good`/`bad`) when the value is
   non-zero; a `0.00` always renders in default ink regardless of the
   `tone` prop passed in, so callers don't need their own zero-check.

## Post-review fixes

Applied after the first in-browser pass, before the live-tint decision
above:

1. **Cluster bottom edges didn't align, and tint didn't cover a whole
   cell.** Root cause was one bug: `MoneyCluster`'s tile row sized itself
   to its own intrinsic content (CSS grid, `grid-cols-2`) instead of
   filling the height the outer 3-col grid had already stretched the
   cluster to — so when Cash's extra "real money put in" sub-caption made
   it taller, Realized/Unrealized's tile rows stayed short, leaving
   unstyled blank space below them (misaligned bottom edge) that also
   wasn't covered by the live tint (tint painted only the tile's own
   content box). Fix: `MoneyCluster` is now `flex h-full flex-col` with
   the tile row as `flex-1`; `MoneyTile` is `flex-1` within that row. Flex's
   default stretch reliably fills the remaining height, so every cluster's
   bottom edge lands on the same line and a tinted tile colors the entire
   cell.
2. Deposit/Withdraw simplified from labeled buttons to plain `+`/`−`
   icon-only buttons (`size="icon-sm"`, `aria-label`s for accessibility),
   still in the Cash cluster header.
