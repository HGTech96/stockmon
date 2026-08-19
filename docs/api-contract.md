# stockmon — API Contract v1.1

Base URL: `http://localhost:8000/api`

## Conventions

- All numbers are raw (no formatting, no currency symbols, no "%" signs). `6.3` means 6.3%. The UI does all formatting.
- All timestamps are ISO 8601 with timezone (`2026-08-19T14:45:00-04:00`). The UI renders them as "Tuesday, 2:45 PM".
- All dates are `YYYY-MM-DD`.
- Every GET response carries a `meta` block (data freshness). The UI shows `dataAsOf` on every page and the stale warning when `isStale` is true. There is no `isRefreshing` server state: refresh is a synchronous POST, so "refreshing" is simply the client awaiting that request.
- `suggestion` labels are machine enums: `"BUY" | "WAIT" | "SELL"`. The UI renders them as "POSSIBLE BUY", "WAIT", "POSSIBLE SELL".
- Checklist items carry a stable machine `id` plus backend-written display `text` — the backend is the single source of wording, so logic and explanation can never diverge.

### `meta` block (on every GET)

```json
{
  "meta": {
    "dataAsOf": "2026-08-19T14:45:00-04:00",
    "isStale": false,
    "staleMessage": null
  }
}
```

When the last refresh failed and old data is served: `"isStale": true`, `"staleMessage": "Couldn't refresh — showing the last known prices from Monday, 4:00 PM."`

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
  "newsLinks": {
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

- Effective target for a position = per-position override if set, else the default.
- (v1.1 candidate: expose the checklist thresholds — RSI cutoff, %-from-low, sharp-move limits — here too, so they're tunable without code changes.)



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
---

## Changelog

### v1.1 (design alignment — after Phase 2 was implemented)
- **A1** Suggestion object: added `metCount` and `totalCount`.
- **A2** `profitTarget`: added `remainingDollars` (uncapped; see Portfolio notes).
- **A3** Insufficient-history state: added `daysOfHistoryRequired` and `tradingDaysUntilReady` alongside `daysOfHistoryAvailable`.
- No endpoint additions or removals. No changes to evaluation rules, checklist ids, thresholds, or precedence — the target-gated exit rule stands as specified in v1.