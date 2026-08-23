# Phase 11a: Remove MoneyStrip from Dashboard

## Context

The Dashboard page currently renders two money-related strips: `SummaryStrip`
(3 tiles: invested / current value / total P&L) and `MoneyStrip` (6 tiles:
cash available, net deposited, realized earned/lost, unrealized gain/loss).
`MoneyStrip` was meant to live on the Portfolio page only, but it's also
mounted on the Dashboard, duplicating it. This phase removes `MoneyStrip`
(and its empty-state sibling `EmptyMoneyStrip`) from the Dashboard page only.
The Portfolio page keeps both strips exactly as they are. No API or contract
changes — `GET /api/stocks` keeps sending the `money` block, Dashboard just
stops rendering it.

Since `MoneyStrip`'s only entry point for opening `CashModal` (the
deposit/withdraw buttons) is being removed from Dashboard, the now-unreachable
`CashModal` wiring on that page (state + import + render) is removed too,
rather than left as dead code (confirmed with user).

## Files to change

```
ui/src/pages/dashboard/DashboardPage.jsx   (edit only)
```

No other files change. `MoneyStrip.jsx`, `EmptyMoneyStrip.jsx`,
`MoneyCluster.jsx`, `MoneyTile.jsx`, and `CashModal.jsx` are untouched —
Portfolio page still uses all of them.

## Changes to DashboardPage.jsx

Remove:
- `import { MoneyStrip } from "../../components/money/MoneyStrip";`
- `import { EmptyMoneyStrip } from "../../components/money/EmptyMoneyStrip";`
- `import { CashModal } from "../../components/money/CashModal";`
- `const [cashModalType, setCashModalType] = useState(null);`
- The `{data.money ? <MoneyStrip .../> : <EmptyMoneyStrip .../>}` block
- The `<CashModal type={cashModalType} .../>` render at the bottom

Keep unchanged:
- `{data.summary && <SummaryStrip summary={data.summary} />}` — this is the
  separate 3-tile strip and stays
- Everything else: header, `RefreshButton`, `StockTable`

## Tasks

- [x] Per CLAUDE.md convention, write this approved plan to
      `docs/planning/phase-11a-remove-dashboard-moneystrip.md`
- [x] Edit `DashboardPage.jsx`: remove `MoneyStrip`/`EmptyMoneyStrip`/`CashModal`
      imports, the `cashModalType` state, the money-strip JSX block, and the
      `CashModal` render
- [x] Remove the `useState` import from `DashboardPage.jsx` (nothing else in
      the file used it)
- [x] Verify Portfolio page (`PortfolioPage.jsx`) is untouched and still
      renders `SummaryStrip`, `MoneyStrip`/`EmptyMoneyStrip`, and `CashModal`
      exactly as before
- [x] Run a build/lint check to confirm Dashboard renders with just the
      `SummaryStrip` + table, no errors from unused imports

## Open questions

None outstanding — CashModal removal on Dashboard was confirmed with the user.
