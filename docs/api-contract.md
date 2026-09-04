# stockmon — API Contract v1.17

Base URL: `http://localhost:8000/api`

## Conventions

- All numbers are raw (no formatting, no currency symbols, no "%" signs). `6.3` means 6.3%. The UI does all formatting.
- All timestamps are ISO 8601 with timezone (`2026-08-19T14:45:00-04:00`). The UI renders them as "Tuesday, 2:45 PM".
- All dates are `YYYY-MM-DD`.
- Every GET response carries a `meta` block (data freshness). The UI shows `dataAsOf` on every page and the stale warning when `isStale` is true. There is no `isRefreshing` server state: refresh is a synchronous POST, so "refreshing" is simply the client awaiting that request.
- `suggestion` labels are machine enums: `"BUY" | "WAIT" | "SELL"`. The UI renders them as "POSSIBLE BUY", "WAIT", "POSSIBLE SELL".
- Checklist items carry a stable machine `id` plus backend-written display `text` — the backend is the single source of wording, so logic and explanation can never diverge.
- `currentPrice` (wherever it appears) reflects a live intraday quote as of
  the last refresh when that refresh ran during market hours; otherwise it's
  the last completed daily close. Value semantics only — the field's shape
  never changed. See Phase 18 (`docs/planning/phase-18-live-current-price.md`).

### `meta` block (on every GET)

```json
{
  "meta": {
    "dataAsOf": "2026-08-19T14:45:00-04:00",
    "isStale": false,
    "staleMessage": null,
    "marketStatus": "open",
    "marketStatusText": "Market Open"
  }
}
```

When the last refresh failed and old data is served: `"isStale": true`, `"staleMessage": "Couldn't refresh — showing the last known prices from Monday, 4:00 PM."`

- `marketStatus` (v1.12): machine enum, `"open" | "pre_market" | "after_hours" | "closed_weekend" | "closed_holiday"` — computed from the current wall-clock time (NYSE regular hours, Eastern time), independent of `dataAsOf`/`isStale`. `marketStatusText` is the backend-owned display string: "Market Open", "Pre-Market Open", "After Hours", "Market Closed" (both closed variants share this text; the enum still distinguishes them).

### Suggestion object

```json
{
  "suggestion": {
    "label": "BUY",
    "type": "entry",
    "metCount": 3,
    "totalCount": 4,
    "checklist": [
      { "id": "price_below_30d_avg",  "text": "Price is below its 30-day average",        "passed": true },
      { "id": "near_30d_low",         "text": "Price is close to its 30-day low",         "passed": true },
      { "id": "rsi_low",              "text": "RSI is relatively low (34)",               "passed": true },
      { "id": "volume_above_avg",     "text": "Trading volume is above average",          "passed": false }
    ],
    "note": null
  }
}
```

- `type`: `"entry"` (BUY/WAIT evaluation) or `"exit"` (SELL evaluation). Determines which checklist is shown.
- `metCount` / `totalCount`: how many checklist conditions passed out of how many — the UI renders "N OF M CONDITIONS MET" from these, never counts client-side.
- `note`: optional extra sentence, e.g. `"Profit target reached — consider your plan."`

**Direction rule (single source of truth, backend-only):**
1. Stock **not owned** → run entry evaluation only. Result: BUY or WAIT, entry checklist.
2. Stock **owned** → run both evaluations. Precedence: exit SELL beats everything; otherwise entry BUY; otherwise WAIT. The returned checklist is the one belonging to the winning label; for WAIT on an owned stock, return the exit checklist.

**Entry checklist ids:** `price_below_30d_avg`, `near_30d_low` (within 5% of 30-day low), `rsi_low` (RSI < 40), `volume_above_avg`. BUY when ≥ 3 pass.

**Exit checklist ids:** `profit_target_reached`, `rsi_high` (RSI > 70), `near_30d_high` (within 5% of 30-day high). SELL when `profit_target_reached` passes **and** at least one technical passes. Target reached alone → WAIT + `note`. Never SELL on a losing position.

### Warning object (sharp-move rule)

Computed once in the backend: 1-day move beyond ±5% **or** 7-day move beyond ±10%.

```json
{ "warning": { "reason": "1d_move", "text": "Sharp recent price move — check the news before acting." } }
```

`null` when not triggered. `reason`: `"1d_move" | "7d_move"`. Dashboard renders it as the row icon, detail page as the orange banner — same field, no client-side re-derivation.

---

## Auth (v1.16)

Session-cookie auth (opaque token, not a JWT). Accounts are admin-created
via `scripts/create_user.py` — there is no self-service signup endpoint.
A missing/invalid/expired session on a protected endpoint returns
`401 { "error": "Not authenticated" }`.

As of v1.17 (23b, see Phase 23 —
`docs/planning/phase-23-multi-user-accounts.md`), every endpoint below
EXCEPT the screener (`GET /api/screener`, `POST /api/screener/refresh`,
`GET /api/screener/{ticker}/detail` — an intentionally separate, shared/
global subsystem per CLAUDE.md) now requires a valid session cookie and
scopes its data to the logged-in user: your own watchlist, trades, cash
ledger, hard-cap settings, and analysis notes. A ticker's shared market
data (price history) is unaffected — refreshing it benefits every user
tracking that ticker. Response shapes are unchanged; the only new
behavior is the `401` case and that two different users now see two
different watchlists/portfolios/histories through the same endpoints.

`POST /api/auth/login`

```json
{ "username": "alice", "password": "hunter2" }
```

→ `200`, sets an httponly `session_id` cookie (30-day fixed expiry):

```json
{ "id": 1, "username": "alice", "email": null }
```

→ `401 { "error": "Invalid username or password" }` on bad credentials.

`POST /api/auth/logout` → `204`, clears the cookie. No-op (still `204`) if
already logged out.

`GET /api/auth/me` → `200`, the same user shape as login; `401` if not
authenticated.

---

## 1. GET /api/stocks — Dashboard

```json
{
  "meta": { "dataAsOf": "2026-08-19T14:45:00-04:00", "isStale": false, "staleMessage": null },
  "summary": {
    "totalInvested": 6812.50,
    "totalCurrentValue": 7284.90,
    "totalProfitLoss": 472.40,
    "totalProfitLossPct": 6.9
  },
  "stocks": [
    {
      "ticker": "AAPL",
      "companyName": "Apple Inc.",
      "currentPrice": 187.42,
      "change1dPct": -1.2,
      "status": "ok",
      "suggestion": "BUY",
      "warning": null,
      "position": { "profitLoss": 111.20, "profitLossPct": 6.3 }
    },
    {
      "ticker": "TSLA",
      "companyName": "Tesla, Inc.",
      "currentPrice": 214.30,
      "change1dPct": -6.4,
      "status": "ok",
      "suggestion": "SELL",
      "warning": { "reason": "1d_move", "text": "Sharp recent price move — check the news before acting." },
      "position": null
    },
    {
      "ticker": "RIVN",
      "companyName": "Rivian Automotive, Inc.",
      "currentPrice": 13.42,
      "change1dPct": 1.1,
      "status": "insufficient_history",
      "suggestion": null,
      "warning": null,
      "position": null
    }
  ]
}
```

- `summary` is `null` when no trades are recorded.
- `status`: `"ok" | "insufficient_history"`. When insufficient, `suggestion` is `null` and the UI shows "Not enough data".
- On the dashboard, `suggestion` is just the label string (checklists live on the detail endpoint).
- `position` is `null` for stocks not owned.
- **Server returns the list pre-sorted:** SELL, BUY, warnings, then WAIT, then insufficient-history. The UI never re-sorts.

## 2. GET /api/stocks/{ticker} — Stock Detail

```json
{
  "meta": { "dataAsOf": "2026-08-19T14:45:00-04:00", "isStale": false, "staleMessage": null },
  "ticker": "AAPL",
  "companyName": "Apple Inc.",
  "currentPrice": 187.42,
  "change1dPct": -1.2,
  "status": "ok",
  "daysOfHistoryAvailable": 43,
  "suggestion": { "label": "BUY", "type": "entry", "metCount": 3, "totalCount": 4, "checklist": [ /* see Suggestion object */ ], "note": null },
  "warning": null,
  "chart": {
    "days": [
      { "date": "2026-07-21", "close": 201.00, "volume": 58200000 },
      { "date": "2026-07-22", "close": 199.40, "volume": 54100000 }
    ],
    "thirtyDayAverage": 194.28,
    "userAvgPurchasePrice": 176.30
  },
  "indicators": {
    "currentPrice": 187.42,
    "change1dPct": -1.2,
    "change7dPct": -3.4,
    "thirtyDayAverage": 194.28,
    "thirtyDayHigh": 203.15,
    "thirtyDayLow": 186.90,
    "distanceFromHighPct": -7.7,
    "distanceFromLowPct": 0.3,
    "rsi": 34.2,
    "todaysVolume": 55900000,
    "averageVolume": 57460000,
    "volumeVsAveragePct": 97.3
  },
  "position": {
    "sharesHeld": 10,
    "avgPurchasePrice": 176.30,
    "amountInvested": 1763.00,
    "currentValue": 1874.20,
    "profitLoss": 111.20,
    "profitLossPct": 6.3,
    "profitTarget": { "targetDollars": 150.00, "progressDollars": 111.20, "remainingDollars": 38.80, "reached": false }
  },
  "analysis": {
    "date": "2026-08-20",
    "value": 210.00,
    "progress": { "targetPrice": 210.00, "progressPrice": 187.42, "remainingPrice": 22.58, "reached": false }
  },
  "newsLinks": {
    "cnnFinance": "https://edition.cnn.com/markets/stocks/AAPL",
    "yahooFinance": "https://finance.yahoo.com/quote/AAPL",
    "googleFinance": "https://www.google.com/finance/quote/AAPL:NASDAQ",
    "investorRelations": "https://investor.apple.com"
  }
}
```

- Price and volume history are **one array** (`chart.days`, 30 entries, oldest first) — they share the time axis; tooltips get date + close + volume from the same row.
- `chart.userAvgPurchasePrice` is `null` when the stock isn't owned (no dashed line).
- **Insufficient history:** `status: "insufficient_history"`, `suggestion: null`, `indicators: null`, `chart: null`. Extra fields for the UI message: `daysOfHistoryAvailable` (e.g. 14), `daysOfHistoryRequired` (30), `tradingDaysUntilReady` (16). `newsLinks` still present.
- `position` is `null` when not owned.
- `analysis` is `null` when no analysis has been recorded for this stock; present regardless of ownership. `analysis.progress` is `null` when `currentPrice` isn't known yet (e.g. never refreshed) — same capped/uncapped shape as `profitTarget` (see `## 7. Analysis`).
- `investorRelations` may be `null` (stored per stock in the `stocks` table; optional).
- 404 for a ticker not on the watchlist.

## 3. GET /api/portfolio

```json
{
  "meta": { "dataAsOf": "2026-08-19T14:45:00-04:00", "isStale": false, "staleMessage": null },
  "hasTrades": true,
  "summary": {
    "totalInvested": 6812.50,
    "totalCurrentValue": 7284.90,
    "totalProfitLoss": 472.40,
    "totalProfitLossPct": 6.9
  },
  "positions": [
    {
      "ticker": "NVDA",
      "companyName": "NVIDIA Corporation",
      "sharesHeld": 25,
      "avgPurchasePrice": 88.10,
      "amountInvested": 2202.50,
      "currentValue": 3213.75,
      "profitLoss": 1011.25,
      "profitLossPct": 45.9,
      "profitTarget": { "targetDollars": 150.00, "progressDollars": 150.00, "remainingDollars": 0.00, "reached": true },
      "status": "ok",
      "suggestion": "SELL"
    }
  ],
  "watchlist": ["AAPL", "NVDA", "MSFT", "KO", "TSLA", "PFE", "DIS", "RIVN"]
}
```

- **Empty state:** `hasTrades: false`, `summary: null`, `positions: []`. `watchlist` is always present (feeds the empty-state text and the trade form dropdown).
- Positions with `sharesHeld` reduced to 0 by sells are **closed** and not listed.
- `progressDollars` is capped at `targetDollars` for display; `reached` is the flag to key off.
- `remainingDollars` = `targetDollars - profitLoss`, floored at 0. NOT derivable from capped `progressDollars` for losing positions (target 300, P/L -198.90 → remaining 498.90) — the UI renders "$X to go" from this field.

## 4. POST /api/trades

Request:

```json
{ "ticker": "AAPL", "action": "buy", "shares": 5, "pricePerShare": 189.10, "date": "2026-08-19" }
```

- `action`: `"buy" | "sell"`.

Response `201`:

```json
{
  "trade": { "id": 17, "ticker": "AAPL", "action": "buy", "shares": 5, "pricePerShare": 189.10, "date": "2026-08-19" },
  "updatedPosition": {
    "ticker": "AAPL",
    "sharesHeld": 15,
    "avgPurchasePrice": 180.57,
    "amountInvested": 2708.50
  }
}
```

- **The backend is the only authority on position math.** The UI's live preview is cosmetic; after submit it displays `updatedPosition` from this response.
- A sell that closes the position returns `"updatedPosition": null`.
- Average-cost rule: buys recompute weighted average price; sells reduce shares and invested amount proportionally, average price unchanged.

Validation → `422` with `{ "error": "<human-readable message>" }`:
- ticker not on watchlist
- `shares <= 0` or `pricePerShare <= 0`
- sell of more shares than currently held
- sell of a stock with no position
- `date` in the future

## 5. POST /api/refresh

Synchronous: downloads latest data for all watchlist tickers via yfinance, upserts `daily_prices`, returns when done (seconds for <20 stocks).

Response `200`:

```json
{
  "refreshed": ["AAPL", "NVDA", "MSFT"],
  "failed": [ { "ticker": "KO", "error": "download timeout" } ],
  "dataAsOf": "2026-08-19T14:45:00-04:00"
}
```

- Partial failure is a `200` — successfully refreshed tickers keep their new data; failed ones serve stale data with `meta.isStale` on their responses.
- Total failure (all tickers failed): still `200` with all in `failed`; subsequent GETs carry the stale meta.

## 6. Settings (profit target)

`GET /api/settings`

```json
{ "defaultProfitTargetDollars": 50.00, "perPositionTargets": { "AAPL": 150.00 } }
```

`PUT /api/settings`

```json
{ "defaultProfitTargetDollars": 50.00 }
```

`PUT /api/settings/targets/{ticker}`

```json
{ "targetDollars": 150.00 }
```

`DELETE /api/settings/targets/{ticker}` (v1.13)
  → 204 (removes the per-position override if one exists; no-op — still
        204 — if the ticker has no override set)
  → 404 { "error": "..." } if ticker not on watchlist

- Effective target for a position = per-position override if set, else the default.
- (v1.1 candidate: expose the checklist thresholds — RSI cutoff, %-from-low, sharp-move limits — here too, so they're tunable without code changes.)

## 7. Analysis (per-stock note)

A personal date + dollar-value note per watchlist stock, independent of
ownership. Nullable, exactly one per stock, purely informational — no effect
on suggestion logic. Shown as the `analysis` block on
`GET /api/stocks/{ticker}` (see section 2), which also carries a computed
`progress` sub-block (`targetPrice`/`progressPrice`/`remainingPrice`/
`reached`) comparing `currentPrice` against the analysis value — same
capped-progress-bar shape as `profitTarget`, `null` when `currentPrice`
isn't known yet. `progress` is NOT present on the `PUT`/`DELETE` responses
below (those return just `date`/`value`); the UI re-fetches the detail
endpoint to see it, same as the hard-cap flow.

`PUT /api/stocks/{ticker}/analysis`

```json
{ "date": "2026-08-20", "value": 210.00 }
```

Response `200` — the updated block:

```json
{ "date": "2026-08-20", "value": 210.00 }
```

- Overwrites any existing value for that ticker.
- 404 for a ticker not on the watchlist.

`DELETE /api/stocks/{ticker}/analysis`

- Clears the analysis back to `null`. `204`. 404 for a ticker not on the watchlist.



---

## Out of contract (v1)

- `GET /api/trades` (trade history list) — data exists in the `trades` table; endpoint deferred until a history page exists.
- Authentication — single local user, none.
- Websockets / push — pull-only; the UI refetches every N minutes via TanStack Query.

## 7. GET /api/trades

All recorded trades, newest first. No pagination.

```json
{
  "meta": { "dataAsOf": "2026-08-19T14:45:00-04:00", "isStale": false, "staleMessage": null },
  "trades": [
    { "id": 18, "ticker": "AAPL", "companyName": "Apple Inc.",
      "action": "sell", "shares": 5, "pricePerShare": 195.00,
      "totalUsd": 975.00, "realizedPnlUsd": 47.50, "date": "2026-08-19" },
    { "id": 17, "ticker": "AAPL", "companyName": "Apple Inc.",
      "action": "buy", "shares": 5, "pricePerShare": 189.10,
      "totalUsd": 945.50, "realizedPnlUsd": null, "date": "2026-08-19" }
  ]
}
```

- `totalUsd` = shares × pricePerShare, computed backend-side.
- `realizedPnlUsd`: sells only — (sale price − average purchase price at the
  time of that sale) × shares sold, computed from the trade log in core.
  `null` on buys.

## Trade editing (v1.4)

PUT /api/trades/{id}
  Request: { "shares": 3, "pricePerShare": 188.00, "date": "2026-08-15" }
  (ticker and action are NOT editable — omitted from the request)
  → 200 { "trade": {...updated...}, "updatedPosition": {...recalculated...} | null }
  → 422 { "error": "..." } if the change makes any later sell of this ticker
        invalid (e.g. reduces an early buy below what a later sell needs)
  → 422 { "error": "..." } basic field validation (shares > 0, price > 0,
        date not in the future) applies as on POST
  → 404 if id not found

DELETE /api/trades/{id}
  → 204
  → 422 { "error": "..." } if deleting would leave a later sell of this
        ticker overselling
  → 404 if id not found

Validation rule (both): after applying the change, replay ALL trades for the
affected ticker in date order; at no point may cumulative sells exceed
cumulative buys. Reject the whole operation if violated — never partially apply.
Because positions are derived, a successful edit/delete automatically corrects
average cost, current position, P/L, portfolio totals, and realized P/L on
later sells with no further action.


# STOCKMON v1.5 -  cash model + P/L breakdown

Append to docs/api-contract.md. Introduces a cash balance, external
deposits/withdrawals, and a six-figure money breakdown. No existing endpoint
shapes are removed; summary objects gain fields.

## Concept: cash

The app now tracks a cash balance — recyclable money held inside the app,
separate from money invested in stocks.

- **Deposit** (external money in): cash increases.
- **Withdraw** (money out to the user's pocket): cash decreases; rejected if
  it exceeds available cash.
- **Buy**: cash decreases by (shares × pricePerShare); REJECTED (422) if it
  exceeds available cash at that point in the trade sequence.
- **Sell**: cash increases by proceeds automatically — recording the sell is
  what returns money to cash.

Deposits and withdrawals are stored as their own event log (a `cash_events`
table), mirroring the event-sourced trades approach: cash balance is DERIVED
by replaying deposits, withdrawals, buys, and sells in chronological order,
never stored as a mutable number.

## Sequence validation (extends the Phase 8 replay)

The trade-sequence replay now tracks TWO running totals per step, in
chronological order across all trades + cash events:
1. Shares per ticker — a sell may never exceed shares held (existing rule).
2. Cash — a buy may never exceed cash available; a withdrawal may never
   exceed cash available (new rule).

Any edit, delete, buy, or withdrawal that would drive either total negative
at any point in the replay is rejected atomically (422), never partially
applied.

**Same-date ordering (deliberate rule):** `cash_events` and `trades` are
separate tables with independent id sequences, so same-date events need an
explicit tie-break to be replayed in a well-defined order. Rule: **money-in
before money-out** — deposits and sells apply before withdrawals and buys on
the same date. This matches how people actually record activity (deposit
then buy same day; sell then withdraw same day) and avoids spuriously
rejecting either. This is a business rule, not a sort-stability detail — do
not change it to id/insertion order.

**Error messages are contextual** — each rejection path has its own wording
so the response tells the user what to do next:

| Path | Message |
|---|---|
| Buy exceeds cash | `Insufficient cash — record a deposit first.` |
| Withdraw exceeds cash | `Can't withdraw more than your available cash.` |
| Deleting a cash event strands a later buy/withdrawal | `Can't remove this — a later buy or withdrawal depends on it.` |
| Editing a trade strands the cash sequence | `Can't make this change — a later buy or withdrawal depends on it.` |
| Deleting a trade strands the cash sequence | `Can't remove this — a later buy or withdrawal depends on it.` |

## The six money figures

Computed backend-side. `money` is a **sibling top-level field** on the GET
/api/stocks (dashboard) and GET /api/portfolio responses — NOT nested inside
`summary`. This matters: `summary` is `null` when `hasTrades` is false (no
positions ever opened), but cash can exist with zero trades (a deposit made,
nothing bought yet) — nesting `money` inside `summary` would hide that cash
balance entirely. `money` is `null` only when there is no cash activity and
no trades at all; otherwise present, independent of `hasTrades`/`summary`.

```json
{
  "meta": { ... },
  "summary": null,
  "money": {
    "cashAvailable": 140.00,
    "netDeposited": 100.00,
    "realizedEarned": 40.00,
    "realizedLost": 0.00,
    "unrealizedGainOpen": 0.00,
    "unrealizedLossOpen": 0.00
  },
  "stocks": [ ... ]
}
```

- `cashAvailable`: current derived cash balance.
- `netDeposited`: total deposits − total withdrawals (real external money in).
- `realizedEarned`: sum of positive realizedPnl across all sells (banked gains).
- `realizedLost`: sum of negative realizedPnl across all sells, as a POSITIVE
  number (banked losses; 0 when none).
- `unrealizedGainOpen`: sum of profitLoss across currently-held positions that
  are positive right now (0 contributes nothing).
- `unrealizedLossOpen`: sum of profitLoss across currently-held positions that
  are negative right now, as a POSITIVE number.

Consistency identity (a built-in correctness check, not a field):
cashAvailable + currentValueOfHoldings
  = netDeposited + realizedEarned − realizedLost
    + unrealizedGainOpen − unrealizedLossOpen

## New endpoints

```
GET /api/cash
  → { "meta": {...},
      "cashAvailable": 140.00,
      "events": [
        { "id": 3, "type": "deposit",  "amountUsd": 100.00, "date": "2026-08-01" },
        { "id": 4, "type": "withdraw", "amountUsd": 20.00,  "date": "2026-08-20" }
      ] }
  (events newest first; buys/sells are NOT listed here — they live in
   /api/trades — this is the external-money log only)

POST /api/cash
  Request: { "type": "deposit" | "withdraw", "amountUsd": 100.00, "date": "2026-08-01" }
  → 201 { "event": {...}, "cashAvailable": 140.00 }
  → 422 { "error": "..." } if withdraw exceeds available cash, amount <= 0,
        or date in the future / creates a negative-cash point in the sequence

DELETE /api/cash/{id}
  → 204
  → 422 if removing the event would drive cash negative at any later point
        (e.g. deleting a deposit that a later buy depended on)
```

## Effect on POST /api/trades (buy)

- A buy is now rejected (422) when it exceeds cashAvailable at its point in
  the sequence: `{ "error": "Insufficient cash — record a deposit first." }`
- Response unchanged otherwise; a successful buy's effect on cash is reflected
  in the next GET.
## Add stock to watchlist (v1.7)

Append to docs/api-contract.md. New watchlist-management endpoint. No
existing endpoint shapes change. Add-only — no removal/archive endpoint.

### POST /api/stocks

Request:

```json
{ "ticker": "PLTR" }
```

- Ticker is uppercased server-side before lookup/storage.

Response `201`:

```json
{ "ticker": "PLTR", "companyName": "Palantir Technologies Inc.", "historyFetched": true }
```

- Validates the ticker resolves via `MarketDataProvider` (company-name
  lookup) — an empty/missing name counts as unresolved, same as a raised
  error. On success, stores the stock and immediately fetches its price
  history (the same per-ticker fetch `POST /api/refresh` uses) so it has
  data right away.
- `historyFetched`: `false` when the name resolved but the immediate history
  fetch failed (e.g. a very new listing with no bars yet) — the stock is
  still added and shows `status: "insufficient_history"` on the dashboard
  until the next refresh. `true` when history came back immediately. The UI
  uses this to word the success toast honestly rather than implying the row
  has data when it doesn't yet.
- `422 { "error": "Unknown ticker — check the symbol." }` — ticker doesn't
  resolve via the provider (raised, or resolved with no usable name).
- `409 { "error": "<TICKER> is already on your watchlist." }` — ticker
  already exists.

## Screener (v1.8, refresh endpoint added in v1.10)

### POST /api/screener/refresh

Synchronous: runs the same batch-fetch+evaluate logic as
`scripts/run_screener.py` against the full screener universe (~150 tickers),
then truncate+rewrites `screener_results` — same underlying function, two
trigger paths. Blocks until the whole run completes (noticeably longer than
`POST /api/refresh`, likely 1–3+ minutes for ~150 tickers).

```json
{
  "refreshed": ["AAPL", "NVDA", "PLTR"],
  "failed": [ { "ticker": "KO", "error": "download timeout" } ],
  "runAt": "2026-08-26T14:45:00-04:00"
}
```

- Partial failure is a `200` — refreshed tickers appear in the new cached
  run, failed ones are simply absent from it (same as a terminal-job run
  that hit a bad ticker). No `meta` field, matching `POST /api/refresh`'s
  shape.
- After this call, `GET /api/screener` reflects the new run immediately.

### GET /api/screener (read-only)

Returns the latest precomputed screener run. Results come from
`scripts/run_screener.py` writing the `screener_results` table; this
endpoint only reads that cache — it never fetches live.

```json
{
  "meta": { "dataAsOf": "2026-08-19T14:45:00-04:00", "isStale": false, "staleMessage": null },
  "runAt": "2026-08-19T09:12:00-04:00",
  "results": [
    {
      "ticker": "PLTR",
      "companyName": "Palantir Technologies Inc.",
      "currentPrice": 27.85,
      "change1dPct": 1.52,
      "change7dPct": 6.30,
      "suggestion": "BUY",
      "metCount": 3,
      "totalCount": 4,
      "rsi": 38.0,
      "priceVs30dAvgPct": -4.1,
      "sharpMove": false,
      "status": "ok"
    }
  ]
}
```

- `suggestion` is entry-only: `"BUY"` or `"WAIT"` (no SELL — no positions in
  the screener universe). Machine enums as elsewhere; UI renders display text.
- `status`: `"ok"` or `"insufficient_history"` (a screener ticker too new for
  30 days of data — `suggestion` null, numeric indicators null, still listed).
- `runAt`: when the screener job last completed. The UI shows "last run …".
- Never-run / empty state:
  ```json
  { "meta": {...}, "runAt": null, "results": [] }
  ```
  The UI shows a "No screen yet" empty state with a "Run screener" button
  (`POST /api/screener/refresh`), distinct from a run that returned rows.

### GET /api/screener/{ticker}/detail

Full detail for ONE screener ticker, computed from a live fetch at request
time. The ticker need NOT be in the tracked watchlist; nothing is persisted.
Payload matches an UNOWNED stock's detail on the main dashboard.

```json
{
  "meta": { "dataAsOf": "2026-08-19T14:45:00-04:00", "isStale": false, "staleMessage": null },
  "ticker": "PLTR",
  "companyName": "Palantir Technologies Inc.",
  "currentPrice": 27.85,
  "change1dPct": 1.52,
  "status": "ok",
  "suggestion": { "label": "BUY", "type": "entry", "metCount": 3, "totalCount": 4, "checklist": [ /* entry checklist */ ], "note": null },
  "warning": null,
  "chart": { "days": [ /* 30 entries: date, close, volume */ ], "thirtyDayAverage": 29.10, "userAvgPurchasePrice": null },
  "indicators": { /* same 12-field shape as the tracked detail endpoint */ },
  "position": null,
  "newsLinks": { "cnnFinance": "...", "yahooFinance": "...", "googleFinance": "...", "investorRelations": null }
}
```

- `position` is always `null` (screener stocks are never owned).
- `chart.userAvgPurchasePrice` always `null` (no position → no cost line).
- `suggestion.type` always `"entry"`; label is BUY or WAIT.
- Computed live via the existing core functions — same analysis as the
  tracked detail, only the price data is sourced from a live fetch instead
  of the DB.
- Insufficient history (a real but too-new ticker): `status:
  "insufficient_history"`, `suggestion: null`, `indicators: null`,
  `chart: null`, the daysOfHistory fields as on the tracked detail;
  `newsLinks` present.
- Ticker the provider can't resolve at all → 422
  `{ "error": "Unknown ticker — check the symbol." }`.

---

## Changelog

### v1.1 (design alignment — after Phase 2 was implemented)
- **A1** Suggestion object: added `metCount` and `totalCount`.
- **A2** `profitTarget`: added `remainingDollars` (uncapped; see Portfolio notes).
- **A3** Insufficient-history state: added `daysOfHistoryRequired` and `tradingDaysUntilReady` alongside `daysOfHistoryAvailable`.
- No endpoint additions or removals. No changes to evaluation rules, checklist ids, thresholds, or precedence — the target-gated exit rule stands as specified in v1.

- v1.4: added PUT/DELETE /api/trades/{id} (edit shares/price/date, or delete;
  full-sequence oversell validation). No changes to evaluation rules.

- v1.5: added cash model (cash_events log, derived balance), GET/POST /api/cash
  and DELETE /api/cash/{id}, six-figure `money` block on dashboard and
  portfolio summaries, and cash tracking in the sequence-replay validation
  (buys and withdrawals cannot oversell cash). No changes to the suggestion/
  evaluation rules.

- v1.6: `shares` now accepts up to 6 decimal places (fractional shares);
  `trades.shares` widened to `Numeric(12,6)`. No endpoint or field shape
  changes — `shares` was always a raw number on the wire, just previously
  whole-number in practice.

- v1.7: added POST /api/stocks (add a ticker to the watchlist). No changes
  to existing endpoint shapes.

- v1.8: added GET /api/screener (cached latest-run screener results,
  entry-only suggestions, never-run state) and GET /api/screener/{ticker}/detail
  (live-fetch full detail for any ticker, unowned-stock shape, nothing
  persisted). No changes to existing endpoints, evaluation rules, or the
  tracked watchlist.

- v1.9: `newsLinks` gains `cnnFinance` (`https://edition.cnn.com/markets/stocks/{TICKER}`,
  CNN's per-ticker quote page — no exchange suffix needed) on both the
  tracked and screener detail endpoints; UI renders it as the first
  news-link button.
  Also: `googleFinance` now includes the exchange suffix (e.g.
  `AAPL:NASDAQ`) resolved via the provider — a value change, not a shape
  change, so no version bump was needed for that half on its own.

- v1.10: added POST /api/screener/refresh — runs the full screener batch job
  on demand (same logic as scripts/run_screener.py) and truncate+rewrites
  screener_results, returning a refreshed/failed/runAt summary shaped like
  POST /api/refresh's response. No changes to GET /api/screener or
  GET /api/screener/{ticker}/detail.

- v1.11: GET /api/screener results gain `change7dPct` (nullable, same source
  as the detail pages' 7-day indicator — null on insufficient_history rows,
  matching rsi/priceVs30dAvgPct). No other changes.

- v1.12: the shared `meta` block (present on every GET response) gains
  `marketStatus` and `marketStatusText` — a clock-based NYSE market-hours
  indicator, independent of data freshness. Additive only; every existing
  `meta` consumer is unaffected. See Phase 19
  (`docs/planning/phase-19-market-status.md`).

- v1.13: added `DELETE /api/settings/targets/{ticker}` (clear a per-position
  profit-target override back to the default; idempotent, 404 only if the
  ticker isn't on the watchlist). No changes to existing settings endpoints
  or evaluation rules — this is the UI-facing "hard cap" feature (display
  wording only; the wire field names `targetDollars`/`profitTarget` are
  unchanged). See Phase 20 (`docs/planning/phase-20-hard-cap-settings.md`).

- v1.14: added a per-stock `analysis` note (date + dollar value, nullable,
  one per stock, independent of ownership) — `analysis` block on
  `GET /api/stocks/{ticker}` (also reused as-is on
  `GET /api/screener/{ticker}/detail`, always `null` there since screener
  tickers aren't on the watchlist), plus
  `PUT`/`DELETE /api/stocks/{ticker}/analysis`. Purely informational, no
  effect on suggestion logic. See Phase 21
  (`docs/planning/phase-21-stock-analysis.md`).

- v1.15: `analysis` gains a computed `progress` sub-block (`targetPrice`/
  `progressPrice`/`remainingPrice`/`reached`, `null` when `currentPrice`
  isn't known) comparing the current price against the analyzed value —
  same shape/capping rule as `position.profitTarget`. Additive; PUT/DELETE
  response shapes unchanged. See Phase 21.

- v1.16: added session-cookie auth — `POST /api/auth/login`,
  `POST /api/auth/logout`, `GET /api/auth/me`. Accounts are admin-created
  (`scripts/create_user.py`), no self-service signup. This version only
  adds the login mechanism (23a); existing endpoints don't yet require or
  scope by it — that's 23b. See Phase 23
  (`docs/planning/phase-23-multi-user-accounts.md`).

- v1.17: every endpoint except the screener now requires the session
  cookie from v1.16 and scopes its reads/writes to the logged-in user
  (watchlist, trades, cash, hard-cap settings, analysis notes). Data model
  split `stocks` into a shared `tickers`/`daily_prices` pair (market data,
  unchanged for everyone tracking a ticker) plus a new per-user
  `watchlist_entries` table; `cash_events`, `settings`, and
  `refresh_status` gained per-user scoping. No response shape changes —
  purely a data-isolation and auth-requirement change. See Phase 23
  (`docs/planning/phase-23-multi-user-accounts.md`).