# Phase 17 — Preserve screener sort/filter across detail navigation

## Overview

Today `/screener` and `/screener/:ticker` are sibling routes (`App.jsx`), so
clicking a row fully unmounts `ScreenerPage`. Its sort/filter state lives in
`useTableViewState`'s own `useState` (`ui/src/hooks/useTableViewState.js`),
so it's gone by the time you navigate back — you land back at the server
default with no filters, even though you never left the screener feature
area.

Fix: lift the sort/filter state one level up, into a small pathless layout
route that wraps only `screener` + `screener/:ticker` (nested inside the
existing `AppShell` route). That route element stays mounted for the whole
"browsing the screener" session — listing and detail both — and only
unmounts when you leave the screener section entirely (nav tabs to
Dashboard/Portfolio/History, or a hard reload). `useTableViewState` gets an
optional 4th argument to accept this externally-owned state instead of its
own; every other table (`StockTable`, `PositionsTable`) is unaffected —
they don't pass it, so they keep today's local-state, reset-on-remount
behavior untouched.

This does **not** change the "reset to server default on reload" rule
(CLAUDE.md) — a reload remounts everything including the new provider, so
state still resets there. It only survives the specific round trip the
request was about: list → row click → detail → back to list.

## Files to create/change

```
ui/src/
├── App.jsx                              (change: nest screener routes under
│                                          a new pathless layout route)
├── components/layout/
│   └── ScreenerSection.jsx              (new: pathless layout route --
│                                          owns sort/filter state, merges it
│                                          into the outlet context alongside
│                                          the existing setMeta)
├── hooks/
│   └── useTableViewState.js             (change: optional 4th `external`
│                                          param -- {sort,setSort,filters,setFilters})
└── pages/screener/
    ├── ScreenerPage.jsx                 (change: read screenerViewState from
    │                                      outlet context, pass to ScreenerTable)
    └── ScreenerTable.jsx                (change: accept + forward `viewState` prop)
```

`ScreenerDetailPage.jsx` needs no change — it already reads `setMeta` via
`useOutletContext()`; it simply ignores the new `screenerViewState` key now
also present in that same context object.

## Schemas / interfaces

```jsx
// ui/src/components/layout/ScreenerSection.jsx
import { useState } from "react";
import { Outlet, useOutletContext } from "react-router-dom";
import { EMPTY_FILTER_STATE } from "../../lib/tableViewState";

/**
 * Pathless layout route wrapping /screener and /screener/:ticker. Holds
 * sort/filter state above both routes so it survives navigating from the
 * table to a row's detail page and back -- CLAUDE.md's table view-state
 * rule (client-side only, reset on reload) still holds; this only changes
 * *when* it resets, from "on every unmount" to "on leaving the screener
 * section or reloading."
 */
export function ScreenerSection() {
  const parentContext = useOutletContext();
  const [sort, setSort] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTER_STATE);

  return <Outlet context={{ ...parentContext, screenerViewState: { sort, setSort, filters, setFilters } }} />;
}
```

```js
// ui/src/hooks/useTableViewState.js
/**
 * @param {{sort, setSort, filters, setFilters}} [external] - when given,
 * state is owned by the caller (e.g. lifted to ScreenerSection) instead of
 * this hook's own useState. Omitted by StockTable/PositionsTable, which
 * keep today's local, reset-on-remount behavior unchanged.
 */
export function useTableViewState(rows, columns, filterConfig, external) {
  const [localSort, setLocalSort] = useState(null);
  const [localFilters, setLocalFilters] = useState(EMPTY_FILTER_STATE);
  const sort = external ? external.sort : localSort;
  const setSort = external ? external.setSort : setLocalSort;
  const filters = external ? external.filters : localFilters;
  const setFilters = external ? external.setFilters : setLocalFilters;
  // ...rest unchanged (toggleSort/setSearch/etc. all just call setSort/setFilters)
}
```

```jsx
// App.jsx
<Route element={<AppShell />}>
  <Route index element={<DashboardPage />} />
  <Route path="stocks/:ticker" element={<StockDetailPage />} />
  <Route path="portfolio" element={<PortfolioPage />} />
  <Route path="history" element={<HistoryPage />} />
  <Route element={<ScreenerSection />}>
    <Route path="screener" element={<ScreenerPage />} />
    <Route path="screener/:ticker" element={<ScreenerDetailPage />} />
  </Route>
</Route>
```

## Task list

- [x] Add optional `external` param to `useTableViewState` (local `useState`
      stays as the fallback storage so Rules of Hooks hold either way)
- [x] Create `ScreenerSection.jsx`, wire into `App.jsx` nesting
- [x] `ScreenerPage.jsx`: destructure `screenerViewState` from
      `useOutletContext()`, pass as `viewState` prop to `ScreenerTable`
- [x] `ScreenerTable.jsx`: accept `viewState` prop, forward as 4th arg to
      `useTableViewState`
- [x] `ScreenerTable.test.jsx`: added a test simulating the unmount/remount
      round trip via an external controlled `viewState` object, confirming a
      sort survives it (`lib/tableViewState.test.js` needed no change --
      pure functions untouched); full vitest suite green (44 passed)
- [x] Manual test: on `/screener`, filtered to "Possible buy" + sorted by
      1-day change (ascending), clicked into NKE's detail page, clicked
      "Back to screener" -- confirmed both the filter chip and sort arrow
      were still applied and row order was unchanged. Then clicked "Clear
      filters" (sort alone persisted, as designed -- they're independent
      state) and confirmed a real `POST /api/screener/refresh` mid-flight
      didn't disturb any of this. Nav-tab-away reset was not separately
      re-verified in this pass (same mechanism as leaving via reload --
      `ScreenerSection` unmounts either way -- low risk, not re-tested live)

## Resolved

Scope confirmed: only the list↔detail round trip preserves state. Leaving
the screener section via a nav tab (Dashboard/Portfolio/History) resets to
server default, same as today, since `ScreenerSection` unmounts in that case.
