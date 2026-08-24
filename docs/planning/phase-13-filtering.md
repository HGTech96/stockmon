# Phase 13 — Table filtering

UI-only. No backend or contract change. Extends the Phase 12 shared
view-state layer with filtering; sort and filter compose (filter narrows
the already-fetched rows, sort orders what remains). Same layer, same
hook, no parallel system.

## Files to create / change

```
ui/src/
├── lib/
│   ├── tableViewState.js             CHANGE  + filterRows, EMPTY_FILTER_STATE, isFilterActive
│   └── tableViewState.test.js        CHANGE  + filter tests, filter+sort combined
├── hooks/
│   └── useTableViewState.js          CHANGE  compose filter -> sort, expose filter state/setters
├── components/
│   └── table/
│       ├── TableFilterBar.jsx        NEW  search input + suggestion chips + optional owned toggle + reset
│       └── NoFilterResults.jsx       NEW  full-width empty-result row ("No stocks match your filters")
└── pages/
    ├── dashboard/
    │   └── StockTable.jsx            CHANGE  filterConfig (incl. owned), <TableFilterBar>, empty-result row
    └── portfolio/
        └── PositionsTable.jsx        CHANGE  filterConfig (no owned toggle), <TableFilterBar>, empty-result row
```

`DashboardPage.jsx` / `PortfolioPage.jsx` stay unchanged — same reasoning as
Phase 12: the tables already own their view-state, so the filter bar lives
in the table shell, not the page.

## Schemas / interfaces

```js
// lib/tableViewState.js (additions — applyTableViewState's existing
// signature and "rows in, rows out, never mutates" contract are untouched)

/**
 * @typedef {Object} FilterConfig
 * @property {(row: any) => string} searchText   - pre-joined lowercased ticker + companyName
 * @property {(row: any) => ("BUY"|"WAIT"|"SELL"|"INSUFFICIENT")} suggestion
 * @property {(row: any) => boolean} [owned]      - omitted on tables with no owned toggle (Portfolio)
 */

/**
 * @typedef {Object} FilterState
 * @property {string} search
 * @property {Set<"BUY"|"WAIT"|"SELL"|"INSUFFICIENT">} suggestions  - empty = no filter
 * @property {"all"|"owned"|"not_owned"} owned    - ignored if FilterConfig.owned is absent
 */

// EMPTY_FILTER_STATE: FilterState                        // { search: "", suggestions: new Set(), owned: "all" }
// filterRows(rows, config: FilterConfig, filters: FilterState) => rows
// isFilterActive(filters: FilterState) => boolean         // drives reset-button visibility
```

```js
// hooks/useTableViewState.js
// useTableViewState(rows, columns, filterConfig) => {
//   rows,                      // filtered THEN sorted
//   sort, toggleSort,          // unchanged from Phase 12
//   filters,                   // FilterState
//   setSearch(text), toggleSuggestion(label), setOwned(value),
//   resetFilters(), isFiltered,
// }
```

```jsx
// components/table/TableFilterBar.jsx
// <TableFilterBar filters onSearch onToggleSuggestion onOwnedChange onReset
//                  showOwnedToggle isFiltered />
// Search input (ticker/company) + BUY/WAIT/SELL/"Not enough data" chips
// (multi-select, reusing SuggestionBadge's exact text + color classes --
// filled when active, muted bg-surface/text-ink-muted when off) +
// owned/not-owned segmented control (dashboard only) + "Clear filters"
// text button, shown only when isFiltered.

// components/table/NoFilterResults.jsx
// <NoFilterResults colSpan onReset />
// Single <tr><td colSpan>...</td></tr> rendered in <tbody> in place of rows
// when filters produced zero matches but the unfiltered table has rows.
```

Column configs unchanged from Phase 12. New filter configs, co-located
next to each table's `COLUMNS`:

- **StockTable**: `searchText` = `ticker + companyName` lowercased ·
  `suggestion` = `"INSUFFICIENT"` when `status === "insufficient_history"`,
  else `s.suggestion` · `owned` = `s.position != null`
- **PositionsTable**: same `searchText`/`suggestion` shape, **no** `owned`
  (every row here is already owned — Portfolio only lists open positions)

## Behavior notes

- Order of operations: `filterRows` first, `applyTableViewState` (sort)
  second — filtering narrows, sort orders what's left. Matches the spec.
- Filters are AND'd together: search AND suggestion-set AND owned.
- Suggestion chips are multi-select (Set); zero selected = show all,
  same "empty = no-op" convention as `sort: null`.
- "Insufficient history" is its own chip (`"INSUFFICIENT"`), never mixed
  into the BUY/WAIT/SELL set — matches `SuggestionBadge`'s existing
  `INSUFFICIENT` variant and the row's own "Not enough data" text.
- Owned/not-owned uses a 3-button segmented control, same visual pattern
  as `TradeModal`'s Buy/Sell toggle (`flex overflow-hidden rounded-lg
  border`, active state tinted, inactive muted).
- No persistence: `filters` (like `sort`) is `useState` local to the hook
  instance — a reload always lands back on server default + no filters.
- Reset clears `search`, `suggestions`, and `owned` together; it does not
  touch `sort` (sorting keeps its own independent 3-state reset already
  built in Phase 12).
- Empty-result row spans all columns (`COLUMNS.length`), distinct from
  Portfolio's existing `EmptyState.jsx` (that one fires on `!hasTrades` —
  no trades recorded at all — and the table isn't rendered in that case,
  so the two states never overlap).
- Styling: raw Tailwind per `TradeModal.jsx` precedent (`rounded-lg`,
  `border-border-strong`, `focus:ring-accent`), not the shadcn `Button`
  primitive.

## Tasks

- [x] `lib/tableViewState.js`: `filterRows`, `EMPTY_FILTER_STATE`, `isFilterActive`
- [x] `lib/tableViewState.test.js`: search (ticker match, company match, case-insensitive, substring) · suggestion filter (one active, multiple active) · insufficient-history as its own filter state · owned/not-owned · filter + sort combined · reset clears all — 28 tests total, all passing
- [x] `hooks/useTableViewState.js`: accept `filterConfig`, compose filter → sort, expose filter state/setters
- [x] `components/table/TableFilterBar.jsx`
- [x] `components/table/NoFilterResults.jsx`
- [x] Wire into `StockTable.jsx` (filterConfig incl. `owned`, filter bar, empty-result row)
- [x] Wire into `PositionsTable.jsx` (filterConfig, no owned toggle, filter bar, empty-result row)
- [x] Manual check: ran the real app (API + UI), verified search (ticker + company name), suggestion chips (single + multiple, incl. "Not enough data"), owned/not-owned toggle, filter+sort combined (My P/L sort held through filter changes), empty-result state on both tables, and reset-clears-filters-but-not-sort on live data

## Resolved (review feedback)

1. Suggestion chips reuse `SuggestionBadge`'s exact text and color classes
   (green/orange/gray + the `INSUFFICIENT` variant) — same vocabulary the
   user already reads in the table, not a second one. Width is handled via
   active/inactive state (filled badge colors when the chip is filtering,
   muted `bg-surface text-ink-muted border-border-strong` when it's off),
   not by shortening labels.
2. `TableFilterBar` sits inside the table shell, directly above `<thead>`
   — same home as sorting. Split: sort + filter ("things that manipulate
   the visible rows") live in the table shell; Add/Refresh ("things that
   change the underlying data") stay page-level. Filter bar ends up
   physically adjacent to the rows it filters.
