# Phase 12 — Table sorting

UI-only. No backend or contract change. Adds a shared, reusable table
view-state layer (sort now, filter plugs into the same layer in Phase 13)
and wires it into the Dashboard and Portfolio tables.

Sorting is a client-side reorder of already-fetched rows — no new API
calls, no persistence, resets to the server default on reload. The server
default order stays the initial state and the state after the third click.

## Files to create / change

```
ui/
├── package.json                          (+ vitest devDependency, "test" script)
└── src/
    ├── lib/
    │   ├── tableViewState.js             NEW  pure sort engine (nulls-last, no mutation)
    │   └── tableViewState.test.js        NEW  vitest unit tests
    ├── hooks/
    │   └── useTableViewState.js          NEW  React state: cycle + apply, no persistence
    ├── components/
    │   └── table/
    │       └── SortableHeaderCell.jsx    NEW  clickable <th>, asc/desc/neutral indicator
    └── pages/
        ├── dashboard/
        │   └── StockTable.jsx            CHANGE  column defs + SortableHeaderCell + hook
        └── portfolio/
            └── PositionsTable.jsx        CHANGE  column defs + SortableHeaderCell + hook
```

`DashboardPage.jsx` / `PortfolioPage.jsx` are unchanged — the tables already
own their row-rendering (they're the closest thing to a "table shell" the
codebase has), so the view-state hook lives there, not in the pages.

No test runner exists in `ui/` today. Adding `vitest` (Vite-native, zero
extra config beyond a `test` block) is the only way to satisfy the "nulls
last / third-click reset" test requirement below — flagged as an open
question in case you'd rather skip frontend tests for this phase.

## Schemas / interfaces

```js
// lib/tableViewState.js
/**
 * @typedef {Object} SortColumn
 * @property {string} key
 * @property {(row: any) => (string|number|null)} accessor
 * @property {"string"|"number"} sortType
 */

/**
 * @typedef {Object} SortState
 * @property {string} key
 * @property {"asc"|"desc"} direction
 */

/**
 * @typedef {Object} ViewState
 * @property {SortState|null} sort
 * // Phase 13 adds a `filters` key here; applyTableViewState's contract
 * // (rows in, rows out, never mutates) does not change.
 */

// applyTableViewState(rows, columns: SortColumn[], viewState: ViewState) => rows
// cycleSort(currentSort: SortState|null, key: string) => SortState|null   // asc -> desc -> null
```

```js
// hooks/useTableViewState.js
// useTableViewState(rows, columns: SortColumn[]) => { rows, sort: SortState|null, toggleSort(key) }
```

```jsx
// components/table/SortableHeaderCell.jsx
// <SortableHeaderCell label sortKey align="left"|"right" sort={sort} onSort={toggleSort} style? />
```

Column configs (co-located in each table file, same pattern as the existing
`HEADERS` array in `PositionsTable.jsx`):

- **StockTable**: ticker (string) · currentPrice (number) · change1dPct
  (number) · suggestion (string, `null` when `insufficient_history`) ·
  position.profitLoss (number, `null` when no position)
- **PositionsTable**: ticker (string) · sharesHeld · avgPurchasePrice ·
  amountInvested · currentValue · profitLoss (all number) ·
  profitTarget.remainingDollars (number) · suggestion (string, `null` when
  `insufficient_history`)

## Behavior notes

- Click cycle: asc → desc → server default (null), same column. Clicking a
  *different* column always starts at asc.
- Nulls (missing suggestion / P/L on insufficient-history rows) sort last
  in both asc and desc — handled by comparing null-ness before direction,
  so direction only flips the ordering of non-null values.
- `Array.prototype.sort` is stable (spec'd since ES2019) — ties keep server
  order, no extra tie-breaker needed.
- Indicator icons: `ChevronUp` / `ChevronDown` (active column) or a faint
  `ChevronsUpDown` (neutral columns), from `lucide-react` — same icon
  library already used for `TriangleAlert`/`Info`/`Plus` elsewhere.
- Header `<th>` becomes clickable + keyboard-focusable (Enter/Space),
  mirroring the existing `StockRow`/`PositionRow` click-and-keydown pattern.

## Tasks

- [x] Add `vitest` to `ui/package.json` devDependencies + `"test": "vitest run"` script (no extra Vite config needed — pure-JS tests run fine on default settings)
- [x] `lib/tableViewState.js`: `applyTableViewState`, `cycleSort`, nulls-last comparator
- [x] `lib/tableViewState.test.js`: numeric column asc/desc, third click → server order, nulls last both directions (string and number columns) — 11 tests, all passing
- [x] `hooks/useTableViewState.js`
- [x] `components/table/SortableHeaderCell.jsx`
- [x] Wire into `StockTable.jsx` (column defs, replace static `<th>`s, sort rows before mapping)
- [x] Wire into `PositionsTable.jsx` (same)
- [x] Manual check: ran the real app (API + UI), clicked Price and My P/L on Dashboard and To target on Portfolio — asc/desc/3rd-click-reset and nulls-last all verified against live data

## Resolved (review feedback)

1. Add `vitest` — approved. Also note the new runner in CLAUDE.md's UI section so future sessions know it exists.
2. `suggestion` column sorts alphabetically by raw label — approved. Third click returns to the server's priority order; the UI's sort stays dumb/alphabetical, the server keeps owning the meaningful ranking.
