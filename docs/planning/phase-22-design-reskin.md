# Phase 22 — Design system reskin

## Overview

Visual/motion reskin only. Every component keeps its current props, data
fetching (React Query), routing, and business logic exactly as-is — only
`className` strings, CSS tokens, and entrance/interaction animation change.

Ground truth is the validated mock at
`/Users/hrachyagumroyan/Projects/claude-designer/work/stockmon` (read-only
reference, not imported). It has Dashboard, Portfolio, and Stock Detail
built out; History, Screener, and Settings were never mocked and get the
same system by extrapolation (match existing density/patterns, don't
invent new ones).

**What's changing:**
- Token swap in `index.css` `@theme` block: warm off-white/brown-gold
  palette → cool gray bg (`#f2f3f6`) + white cards + teal accent
  (`#0891b2`), distinct bg vs. surface for actual depth, `shadow-card`/
  `shadow-pop` for elevation instead of relying on a hairline border.
- `Button.jsx`: replace the `@base-ui/react` primitive + cva setup with a
  plain `forwardRef<button>` in the reference's raw-Tailwind pattern, but
  keep 4 variants (primary/outline/ghost/**destructive**, solid
  `bg-bad text-white`, same weight as primary — not the tinted
  `bg-bad-bg`/`text-bad` badge treatment) and the full size scale
  (xs/sm/md/lg/icon-xs/icon-sm/icon-lg), extending the reference's
  sm/md/icon-sm formula rather than collapsing existing size diversity.
  Confirmed prior direction — this primitive was already flagged as tech
  debt to move away from in favor of the raw-Tailwind button pattern.
- Badges/chips go `rounded-pill` → `rounded-sm` (sharp, not pill-shaped).
- New dependency: `motion` (npm package, imported as `motion/react`) for
  table-row stagger, modal/toast/banner enter-exit, and page crossfade.
  Recharts' built-in line animation gets turned back on
  (`isAnimationActive` currently forced `false`).
- New: `LiveDot` component (pulsing freshness indicator), noise-overlay
  div in `AppShell`, price-flash-on-update effect in table rows.
- Everything else (query hooks, route structure, prop shapes, validation,
  API calls) is untouched.

## New dependency

```
ui/package.json
  + "motion": "^12.x"   (motion/react — NOT framer-motion, NOT GSAP)
```

## Token diff (`ui/src/index.css` `@theme` block)

Full replacement values are in the prompt/reference `index.css` — copied
1:1, including the new `--color-*` set (bg/surface/surface-sunken/
surface-hover/border/border-strong/ink tiers/accent tiers/good/warn/
neutral/bad + bg/border pairs), `--radius-sm: 6px` (new), `--shadow-card`,
`--shadow-pop`. Font stack (Public Sans / JetBrains Mono) and the `.num`
utility are unchanged. shadcn primitive aliases
(`--color-primary`, `--color-muted`, etc.) get repointed at the new tokens,
same as today's pattern.

## Files to create/change

```
ui/
  package.json                              (+ motion dependency)
  src/
    index.css                               (token replacement, see above)
    components/
      ui/
        button.jsx                          (rewrite: drop @base-ui primitive, keep
                                              4 variants incl. destructive + full size scale)
        dialog.jsx                          (restyle only: keep base-ui Dialog primitive
                                              for focus trap/Escape/scroll-lock/portal;
                                              retheme classNames + controlled-open
                                              AnimatePresence wrapper on DialogContent/backdrop)
      badge/
        SuggestionBadge.jsx                 (rounded-sm, updated classes)
        ActionBadge.jsx                     (match badge convention)
      layout/
        AppShell.jsx                        (bg/surface split, noise overlay, page crossfade)
        NavTabs.jsx                         (accent underline/active state, active:translate-y-px)
        FreshnessBar.jsx                    (pairs with new LiveDot)
        MarketStatusBadge.jsx               (rounded-sm chip convention)
        LiveDot.jsx                         (NEW — pulsing dot, useReducedMotion guarded)
        ScreenerSection.jsx                 (card convention)
      money/
        MoneyStrip.jsx, MoneyCluster.jsx, MoneyTile.jsx, EmptyMoneyStrip.jsx, CashModal.jsx
                                             (gap-px bg-border divider pattern, h-9 fixed
                                              header row, deposit=good/withdraw=bad tint,
                                              modal → AnimatePresence)
      panel/Panel.jsx                       (card convention)
      summary/SummaryStrip.jsx              (gap-px bg-border divider pattern)
      table/
        SortableHeaderCell.jsx, TableFilterBar.jsx, NoFilterResults.jsx
                                             (surface-sunken header, accent sort state)
      toast/Toast.jsx                       (AnimatePresence, semantic tone colors)
      tooltip/InfoTooltip.jsx               (surface/shadow-pop)
      trend/Trend.jsx                       (good/bad tone only, .num)
      checklist/SuggestionChecklist.jsx     (card convention)
      charts/PriceVolumeChart.jsx           (enable isAnimationActive, gradient Area fill)
    pages/
      dashboard/                            (StockTable.jsx row stagger + price-flash,
                                              StockRow.jsx, AddStockModal.jsx, RefreshButton.jsx,
                                              AddStockButton.jsx)
      portfolio/                            (PositionsTable.jsx, PositionRow.jsx, TradeModal.jsx,
                                              EmptyState.jsx — TradeModal is the raw-button
                                              pattern source, keep its interaction model)
      stock-detail/                         (DetailHeader.jsx, PositionCard.jsx,
                                              IndicatorsPanel.jsx, AnalysisCard.jsx,
                                              AnalysisModal.jsx, HardCapModal.jsx,
                                              WarningBanner.jsx, NewsLinksPanel.jsx,
                                              InsufficientHistoryPanel.jsx)
      history/                              (TradeHistoryTable.jsx, TradeHistoryRow.jsx,
                                              EditTradeModal.jsx, DeleteTradeConfirm.jsx,
                                              EmptyState.jsx — extrapolated, no mock)
      screener/                             (ScreenerTable.jsx, ScreenerRow.jsx,
                                              ScreenerRefreshButton.jsx, ScreenerEmptyState.jsx
                                              — extrapolated, no mock)
      screener-detail/ScreenerDetailPage.jsx, TrackStockButton.jsx
                                             (extrapolated, no mock)
      settings/                             (SettingsPage.jsx, DefaultCapForm.jsx,
                                              OverridesList.jsx — extrapolated, no mock)
    App.jsx                                 (page-level AnimatePresence mode="wait" crossfade)
docs/plan.md                                (add Phase 22 entry)
```

No changes to `ui/src/api/`, `ui/src/hooks/useDataRefresh.js`,
`ui/src/hooks/useTableViewState.js`, `ui/src/lib/tableViewState.js`,
`ui/src/lib/format.js`, or any test file's assertions (tests target
behavior/logic, not classNames, so they should keep passing unmodified —
flagged as a check, not a rewrite target).

## Task list

- [x] Add `motion` dependency; confirm dev server + build still run
- [x] Replace `index.css` `@theme` tokens (bg/surface/accent/semantic/
      radius/shadow) and shadcn alias repoints; verify no hardcoded hex
      remains in components after the pass (grep check)
- [x] Rewrite `button.jsx` off the `@base-ui/react` primitive to a plain
      raw-Tailwind `forwardRef<button>`, keeping 4 variants
      (primary/outline/ghost/destructive — destructive solid `bg-bad`,
      full weight, not a tint) and the full xs/sm/md/lg/icon-xs/icon-sm/
      icon-lg size scale; audit call sites for now-removed variant names
      only (`default`→primary, `secondary`→outline or ghost by context,
      `link` if used anywhere)
- [x] `SuggestionBadge.jsx`, `ActionBadge.jsx`, `MarketStatusBadge.jsx`:
      `rounded-pill` → `rounded-sm`, size/class updates
- [x] `AppShell.jsx` + `NavTabs.jsx` + `FreshnessBar.jsx` + new
      `LiveDot.jsx`: shell chrome, noise overlay, live indicator
- [x] `SummaryStrip.jsx`, `MoneyStrip.jsx`/`MoneyCluster.jsx`/
      `MoneyTile.jsx`/`EmptyMoneyStrip.jsx`: divider-via-gap pattern,
      fixed `h-9` header row, deposit/withdraw semantic tint
- [x] Dashboard page + `StockTable.jsx`/`StockRow.jsx`: row stagger on
      mount/filter-change, price-flash-on-update (CSS transition on
      inline `style.backgroundColor`, not Motion `animate` prop — the
      variants/animate conflict noted in the brief)
- [x] Portfolio page + `PositionsTable.jsx`/`PositionRow.jsx`/
      `TradeModal.jsx`
- [x] Stock Detail page + all its panels/cards + `PriceVolumeChart.jsx`
      (animation on, gradient Area fill)
- [x] Modals/toast pass: `AddStockModal`, `TradeModal`, `CashModal`,
      `EditTradeModal`, `DeleteTradeConfirm`, `AnalysisModal`,
      `HardCapModal`, `Toast.jsx`, `dialog.jsx` retouched. `dialog.jsx`
      uses base-ui's own `data-open`/`data-closed` CSS-transition hook
      (scale/y/opacity, ~0.2s easeOut) instead of wrapping
      `AnimatePresence` around it — forcing Motion's presence-control
      into base-ui's own unmount-on-transition-end lifecycle risked the
      two fighting over who owns visibility state; the visual result is
      identical. `Toast.jsx` uses real `AnimatePresence` (own hand-rolled
      element, no such conflict).
- [x] History page (extrapolated)
- [x] Screener + Screener Detail pages (extrapolated)
- [x] Settings page (extrapolated)
- [x] `App.jsx` page-level crossfade implemented in `AppShell.jsx`
      (wraps `<Outlet/>`, not `App.jsx`'s `<Routes>`, since that's the
      one spot shared by every route) via `AnimatePresence mode="wait"`.
      Key is collapsed to `"screener"` for both `/screener` and
      `/screener/:ticker` so `ScreenerSection`'s lifted sort/filter state
      (Phase 17) survives that internal nav instead of remounting.
- [x] Full pass: verify `prefers-reduced-motion` respected on every new
      animation (LiveDot, row stagger, modals) — all via Motion's
      `useReducedMotion()`/declarative variants, consistent with the
      existing app pattern.
- [x] Manual check at 375px (mobile) and 1440px (desktop) via the local
      dev server + real seeded data for Dashboard, Portfolio, Stock
      Detail, History, Screener, Settings, and the Add-trade modal.
- [x] `npm test` (ui, 44 tests), `npm run lint`, and `npm run build` all
      green.
- [x] Marked this file's checkboxes and `docs/plan.md`'s Phase 22 entry
      done.

## Resolved

1. **Button.** `destructive` stays as a real 4th variant (solid `bg-bad
   text-white`, same weight as `primary` — not the tinted badge
   treatment), for delete-trade/clear-analysis actions where color-coding
   danger is load-bearing UX. Full size scale (xs/sm/md/lg/icon-xs/
   icon-sm/icon-lg) carries over unchanged rather than collapsing to the
   mock's 3 — the mock's set was just what that page needed, not a ceiling.
2. **`dialog.jsx`.** Restyle only — keep the base-ui `Dialog` primitive
   for focus trap/Escape/scroll-lock/portal (the mock's hand-rolled
   `AnimatePresence` divs have none of that, fine for a throwaway visual
   mock, not fine to ship). Retheme classNames (`bg-surface`,
   `shadow-pop`, `rounded-DEFAULT`, `border-border-strong`, `p-6`) and
   layer Motion on top via controlled `open` state + `AnimatePresence`
   wrapping `DialogContent`/backdrop (scale 0.97→1, y 12→0, opacity,
   ~0.2s easeOut) — the standard Radix/base-ui + Framer controlled-open
   pattern.
3. **History/Screener/Settings have no mock.** Proceeding with
   extrapolation from the nearest built page (History tables →
   Dashboard/Portfolio table patterns; Settings forms → modal form
   patterns), reviewed in-browser before locking in, per default proposed
   and not objected to.
