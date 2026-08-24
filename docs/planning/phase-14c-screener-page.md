# Phase 14c — Screener frontend (page + click-through + promote)

## Context

Phases 14a/14b shipped the screener backend: `GET /api/screener` (cached
latest-run results, entry-only BUY/WAIT, never-run state) and
`GET /api/screener/{ticker}/detail` (live-fetch, identical shape to an
**unowned** tracked-stock detail response). This phase is the UI-only
finish: a separate `/screener` page and detail view that read those two
endpoints, reusing the Phase 12/13 table view-state layer, `SuggestionBadge`,
the detail-page shell components, and the Phase 11b add-stock flow — no new
backend, no contract change, no new business logic in the UI.

The screener stays a clearly separate tool from the tracked watchlist per
CLAUDE.md: its own nav tab, its own route, its own cache; a stock only joins
the tracked watchlist through the explicit "Track this stock" action.

## Decisions

1. **Test strategy** — the repo has no component-rendering test setup today
   (CLAUDE.md scopes vitest to pure logic only; Phase 12/13 verified table
   wiring manually in the browser). The requested test list (render, sort/
   filter, both empty states, row navigation, track-stock flow) needs real
   component rendering, so this phase adds `@testing-library/react`,
   `@testing-library/jest-dom`, `@testing-library/user-event`, and `jsdom`
   as new devDependencies, plus a `jsdom` test environment in
   `vite.config.js`. This is new testing capability for the project, not
   just new test files — flagging since CLAUDE.md's "Don't" list warns
   against unasked-for additions; approved as part of this plan's review.
2. **"Track this stock" is a direct button, not a re-opened modal** — the
   ticker is already known and already resolved (the page only renders once
   the live fetch succeeded), so re-showing `AddStockModal`'s free-text
   ticker input would be redundant friction. `TrackStockButton` calls the
   same `addStock()` API function and reuses the same toast wording/tones
   as `AddStockModal` — same flow, same endpoint, same messages, no modal.

## Files to create/change

```
ui/
├── package.json                          CHANGE  + @testing-library/react,
│                                                    jest-dom, user-event, jsdom
├── vite.config.js                        CHANGE  + test.environment = "jsdom"
└── src/
    ├── api/
    │   ├── screener.js                   NEW     getScreener(), getScreenerDetail(ticker)
    │   └── types.js                      CHANGE  + ScreenerResult, ScreenerResponse typedefs
    ├── lib/
    │   ├── format.js                     CHANGE  + fmtRelativeTime()
    │   └── format.test.js                NEW     fmtRelativeTime tests
    ├── components/layout/
    │   └── NavTabs.jsx                   CHANGE  + Screener tab
    ├── App.jsx                           CHANGE  + /screener, /screener/:ticker routes
    └── pages/
        ├── screener/
        │   ├── ScreenerPage.jsx          NEW     fetch + header + never-run empty state
        │   ├── ScreenerTable.jsx         NEW     COLUMNS + FILTER_CONFIG + view-state hook
        │   ├── ScreenerRow.jsx           NEW     one row (8 columns incl. sharp-move icon)
        │   ├── ScreenerEmptyState.jsx    NEW     "No screen yet — run scripts/run_screener.py"
        │   └── ScreenerTable.test.jsx    NEW     RTL: rows, sort, filter, filtered-empty, row nav
        └── screener-detail/
            ├── ScreenerDetailPage.jsx    NEW     mirrors StockDetailPage, feeds off 14b endpoint
            ├── TrackStockButton.jsx      NEW     direct addStock() call + toast (no modal)
            └── ScreenerDetailPage.test.jsx  NEW  RTL: never-run vs run, track-stock success/409
```

Everything else is reused unchanged: `useTableViewState`, `tableViewState.js`,
`SortableHeaderCell`, `TableFilterBar`, `NoFilterResults`, `SuggestionBadge`,
`DetailHeader`, `SuggestionChecklist`, `PriceVolumeChart`, `IndicatorsPanel`,
`WarningBanner`, `InsufficientHistoryPanel`, `NewsLinksPanel`, `Panel`,
`Trend`, `Toast`/`useToast`, `addStock()` from `api/stocks.js`.

## Schemas / interfaces

```js
// api/types.js — additions (mirrors docs/api-contract.md v1.8)
/**
 * @typedef {Object} ScreenerResult
 * @property {string} ticker
 * @property {string} companyName
 * @property {number} currentPrice
 * @property {number} change1dPct
 * @property {"BUY"|"WAIT"|null} suggestion
 * @property {number|null} metCount
 * @property {number|null} totalCount
 * @property {number|null} rsi
 * @property {number|null} priceVs30dAvgPct
 * @property {boolean|null} sharpMove
 * @property {"ok"|"insufficient_history"} status
 */
/**
 * @typedef {Object} ScreenerResponse
 * @property {Meta} meta
 * @property {string|null} runAt
 * @property {ScreenerResult[]} results
 */
// Screener detail reuses StockDetailResponse as-is (contract: identical
// shape, position always null) — no new typedef needed.
```

```js
// api/screener.js
import { request } from "./client";
/** @returns {Promise<import('./types').ScreenerResponse>} */
export function getScreener() { return request("/screener"); }
/** @param {string} ticker @returns {Promise<import('./types').StockDetailResponse>} */
export function getScreenerDetail(ticker) { return request(`/screener/${ticker}/detail`); }
```

```js
// lib/format.js addition
/** @param {string} isoDatetime @returns {string} "Just now" | "5m ago" | "3h ago" | "2d ago" */
export function fmtRelativeTime(isoDatetime) { ... }
```

```js
// pages/screener/ScreenerTable.jsx
const COLUMNS = [
  { key: "ticker", label: "Stock", sortType: "string", accessor: r => r.ticker },
  { key: "currentPrice", label: "Price", sortType: "number", accessor: r => r.currentPrice },
  { key: "change1dPct", label: "1-day change", sortType: "number", accessor: r => r.change1dPct },
  { key: "suggestion", label: "Suggestion", sortType: "string",
    accessor: r => (r.status === "insufficient_history" ? null : r.suggestion) },
  { key: "metCount", label: "Conditions met", sortType: "number", accessor: r => r.metCount },
  { key: "rsi", label: "RSI", sortType: "number", accessor: r => r.rsi },
  { key: "priceVs30dAvgPct", label: "vs 30d avg", sortType: "number", accessor: r => r.priceVs30dAvgPct },
  { key: "sharpMove", label: "Move", sortType: "number", accessor: r => (r.sharpMove == null ? null : Number(r.sharpMove)) },
];
const FILTER_CONFIG = {
  searchText: r => `${r.ticker} ${r.companyName}`,
  suggestion: r => (r.status === "insufficient_history" ? "INSUFFICIENT" : r.suggestion),
  // no `owned` key, no showOwnedToggle — screener stocks are never owned
};
```

```jsx
// pages/screener-detail/TrackStockButton.jsx
/** @param {{ ticker: string, showToast: (msg: string, tone?: "good"|"neutral") => void }} props */
export function TrackStockButton({ ticker, showToast }) {
  const mutation = useMutation({
    mutationFn: () => addStock(ticker),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["stocks"] });
      showToast(data.historyFetched
        ? `${data.ticker} added to your watchlist.`
        : `${data.ticker} added — price data will load on the next refresh.`, "good");
    },
    onError: (err) => showToast(err.message, "neutral"), // covers 409 and the rare 422
  });
  // disabled once isPending || isSuccess; label "Track this stock" / "Adding…" / "Added"
}
```

## Behavior notes

- **Row rendering**: ticker+company, price (`fmtPrice`), 1-day change
  (`<Trend/>`), suggestion (`<SuggestionBadge label={result.suggestion}/>`
  or muted "Not enough data" text when `status === "insufficient_history"` —
  same branch `StockRow` already uses), conditions-met as `"N of M"` text or
  dash, RSI/vs-30d-avg via `fmtOrDash`, sharp-move as a `TriangleAlert` icon
  when `true`, nothing when `false`, dash when `null`.
- **Never-run vs. filtered-empty**: `ScreenerPage` branches on `runAt ===
  null` and swaps the **entire table shell** for `ScreenerEmptyState`
  (mirrors `PortfolioPage`'s `hasTrades` branch) — no CTA button, since the
  screener page never triggers the batch job itself (CLAUDE.md). Filtered-
  to-zero-rows (a real run, filters exclude everything) stays inside
  `ScreenerTable` via the existing shared `NoFilterResults`, unmodified —
  the two states never overlap, same reasoning as Phase 13.
- **"Last screened"**: `ScreenerPage` shows `Last screened {fmtRelativeTime(runAt)}`
  next to the row count, only when `runAt` is present. The top freshness bar
  still calls `setMeta(data?.meta)` like every other page (that's the
  tracked-watchlist's freshness per the contract's shared `meta` convention)
  — two different timestamps, two different UI spots, no conflation.
- **Detail page reuse**: `ScreenerDetailPage` is a parallel file to
  `StockDetailPage` (not a shared generalized component — two call sites,
  matches the existing one-table-per-page pattern), swapping
  `getStockDetail(ticker)` for `getScreenerDetail(ticker)` and the query key
  to `["screenerDetail", ticker]`. `data.position` is always `null`, so the
  position-card branch simply never renders — no extra conditional needed
  beyond what `StockDetailPage` already does. Back link points to
  `/screener` ("Back to screener") instead of `/`.
- **Track this stock placement**: rendered top-right of the page header, next
  to the back link — mirrors how `AddStockButton`/`RefreshButton` sit
  together on `DashboardPage` — rather than buried where `PositionCard`
  would have been, since it's this page's primary call to action. Visible in
  both the `ok` and `insufficient_history` branches (tracking a stock with
  thin history is already a supported state on the main dashboard).
  `ScreenerDetailPage` owns its own `useToast()`/`<Toast/>` instance, same
  as `DashboardPage` — toasts aren't a shared cross-page system.
- **Styling**: raw Tailwind per `TradeModal.jsx`/`AddStockModal.jsx`
  precedent for `TrackStockButton` — not the shadcn `Button` primitive.
- **Nav**: add `{ to: "/screener", label: "Screener", end: false }` to
  `NavTabs.jsx`'s `TABS` array — `end: false` so `/screener/AAPL` still
  highlights the tab, same convention already used for Portfolio/History.

## Tasks

Setup
- [x] `package.json`: add `@testing-library/react`, `@testing-library/jest-dom`,
      `@testing-library/user-event`, `jsdom` devDependencies
- [x] `vite.config.js`: add `test: { environment: "jsdom" }`

API layer
- [x] `api/screener.js`: `getScreener()`, `getScreenerDetail(ticker)`
- [x] `api/types.js`: `ScreenerResult`, `ScreenerResponse` typedefs
- [x] `lib/format.js` + `format.test.js`: `fmtRelativeTime()`

Screener list page
- [x] `pages/screener/ScreenerRow.jsx`
- [x] `pages/screener/ScreenerTable.jsx` (COLUMNS, FILTER_CONFIG, `useTableViewState`, reused `TableFilterBar`/`SortableHeaderCell`/`NoFilterResults`)
- [x] `pages/screener/ScreenerEmptyState.jsx`
- [x] `pages/screener/ScreenerPage.jsx` (fetch, header + "Last screened", never-run branch, `setMeta`)
- [x] `pages/screener/ScreenerTable.test.jsx`: renders rows from fixture data; column sort asc/desc/reset; search + suggestion filter narrow rows via the shared layer; filtered-to-empty shows `NoFilterResults`; row click navigates to `/screener/:ticker` — 6 tests, all passing

Screener detail page
- [x] `pages/screener-detail/TrackStockButton.jsx`
- [x] `pages/screener-detail/ScreenerDetailPage.jsx`
- [x] `pages/screener-detail/ScreenerDetailPage.test.jsx`: insufficient-history branch renders `InsufficientHistoryPanel`; ok branch renders chart/indicators/checklist; `TrackStockButton` success calls `addStock` + shows success toast + invalidates `["stocks"]`; 409 shows the neutral toast — 4 tests, all passing

Wiring
- [x] `App.jsx`: add `screener` and `screener/:ticker` routes inside `AppShell`
- [x] `components/layout/NavTabs.jsx`: add the Screener tab
- [x] Manual check (real API + UI, via Chrome): never-run empty state verified before running the job; ran `scripts/run_screener.py` against a temporary 4-ticker universe (AAPL/TSLA/RIVN/PLTR, universe file restored immediately after); verified results table (sort by Price asc/desc/reset, search filter, suggestion chip filter, filtered-empty vs. never-run distinction), "Last screened Just now" text, row click → detail (chart/checklist/news links rendered from the live 14b endpoint), "Track this stock" 409 toast on an already-tracked ticker (AAPL), and the success path on an untracked screener ticker (RIVN) — green toast, button → "Added", and RIVN confirmed present via `GET /api/stocks` immediately after. Test artifacts (RIVN watchlist row + its price history, the 4-ticker screener_results cache) removed from the dev DB afterward and the watchlist/screener cache verified back to their pre-test state (15 tracked stocks, never-run screener) — same manual-check discipline as Phase 11b.
- [x] Mark completed items in `docs/plan.md` Phase 14c

Full suite: `npm test` — 43/43 passing across 4 files. `npm run lint` clean (one pre-existing unrelated warning). `npm run build` succeeds.

## Open questions

None outstanding — test-infra and track-stock UX were resolved above during
planning review.
