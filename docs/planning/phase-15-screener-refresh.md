# Phase 15 — Screener refresh button

## Overview

Add a "Refresh" button to the screener page that re-runs the full ~150-ticker
screener batch on demand, instead of only via the manual terminal job. This is
an intentional change to the CLAUDE.md rule that "the screener page never
triggers the batch fetch itself" (confirmed with the user) — CLAUDE.md has
already been updated to reflect it.

The batch-fetch loop currently lives inline in `scripts/run_screener.py`'s
`main()`. It moves into `screener_service.py` as a shared function so both the
terminal script and the new endpoint call the same code — same pattern as
`POST /api/refresh` for the tracked watchlist (synchronous, blocks until
done, no job queue).

**No change** to `GET /api/screener` or `GET /api/screener/{ticker}/detail` —
this only adds one new endpoint.

## Files to create/change

```
api/src/stockmon/
├── services/
│   └── screener_service.py       (change: add run_screener_batch(); move
│                                   BATCH_SIZE/BATCH_PAUSE_SECONDS here)
├── api/
│   ├── routes/screener.py        (change: add POST /api/screener/refresh)
│   └── schemas/screener.py       (change: add ScreenerRefreshResponse)
api/scripts/
└── run_screener.py               (change: main() calls run_screener_batch();
                                    drop the now-moved constants/loop)
docs/
└── api-contract.md               (change: v-bump, document POST /api/screener/refresh)
ui/src/
├── api/
│   └── screener.js               (change: add postScreenerRefresh())
└── pages/screener/
    ├── ScreenerPage.jsx          (change: render ScreenerRefreshButton)
    ├── ScreenerEmptyState.jsx    (change: replace terminal instruction with
    │                              ScreenerRefreshButton, label "Run screener")
    └── ScreenerRefreshButton.jsx (new: button + mutation + inline failure notice)
```

## Schemas / interfaces

```python
# api/src/stockmon/services/screener_service.py

BATCH_SIZE = 10
BATCH_PAUSE_SECONDS = 1.5

@dataclass(frozen=True)
class ScreenerBatchResult:
    rows: list[ScreenerRow]
    failures: list[ScreenerFetchFailure]
    run_at: datetime

def run_screener_batch(provider: MarketDataProvider) -> ScreenerBatchResult:
    """Reads screener_stocks.txt, fetches+evaluates in batches (same
    ThreadPoolExecutor-per-batch logic currently in run_screener.py),
    does NOT touch the DB. Caller persists via save_screener_run."""
```

```python
# api/src/stockmon/api/schemas/screener.py

class ScreenerRefreshFailureSchema(BaseModel):
    ticker: str
    error: str

class ScreenerRefreshResponse(BaseModel):
    refreshed: list[str]
    failed: list[ScreenerRefreshFailureSchema]
    runAt: str  # ISO timestamp
```

```
POST /api/screener/refresh

Response 200:
{
  "refreshed": ["AAPL", "NVDA", ...],
  "failed": [ { "ticker": "KO", "error": "download timeout" } ],
  "runAt": "2026-08-26T14:45:00-04:00"
}
```

- Synchronous: blocks until the whole universe (~150 tickers) is fetched —
  same partial-failure contract as `POST /api/refresh` (always `200`,
  failed tickers just don't appear in `refreshed`).
- On completion, `save_screener_run` does its usual truncate+rewrite —
  **partial** failures still replace the whole cache (rows that fail simply
  aren't in the new set, same as today's terminal-job behavior — the table
  reflects "current run", not "best of last two runs").
- No `meta` field — matches `POST /api/refresh`'s existing shape, no precedent
  in this codebase for wrapping a mutation response in `meta`.

```js
// ui/src/api/screener.js
/** @returns {Promise<import('./types').ScreenerRefreshResponse>} */
export function postScreenerRefresh() { ... }

// ui/src/api/types.js (new typedefs, same shape family as RefreshResponse)
/** @typedef {{ ticker: string, error: string }} ScreenerRefreshFailure */
/** @typedef {{ refreshed: string[], failed: ScreenerRefreshFailure[], runAt: string }} ScreenerRefreshResponse */
```

No new formatting helper needed — `fmtRefreshSummary` in `lib/format.js`
already only reads `.refreshed.length` / `.failed`, so it works unchanged
for this response shape too.

## Behavior

- Button sits next to the "N stocks screened · Last screened …" line in
  `ScreenerPage.jsx`'s header row (`justify-between`), right-aligned —
  same placement pattern as the dashboard's `RefreshButton`.
- Rendered even in the never-run empty state (`ScreenerEmptyState.jsx`) —
  replaces the "run scripts/run_screener.py from the terminal" instruction
  with the same button (label "Run screener" in that state vs. "Refresh"
  once a run exists), so a first run no longer requires the terminal.
- Click → `useMutation(postScreenerRefresh)`.
  - Pending: disabled, label → `"Refreshing…"` (same label-swap convention,
    raw-Tailwind button, not the shadcn primitive — matches `RefreshButton`
    and the memory note on this).
  - Success: invalidate `["screener"]` so the table and "Last screened"
    timestamp refetch from the now-updated cache.
  - `fmtRefreshSummary(result)` non-null → inline warn-toned notice below the
    button (same `border-warn-border bg-warn-bg text-warn` box, names failed
    tickers) — identical pattern to `RefreshButton`.
  - Mutation error (network/non-2xx) → same warn box with thrown message.
- Given ~150 tickers at batch-size 10 with a 1.5s pause, a full run takes
  noticeably longer than the tracked-watchlist refresh (likely 1–3+ minutes
  depending on fetch latency) — the button stays disabled/dimmed the whole
  time, no progress bar (no precedent for one anywhere in this app; honest
  "Refreshing…" state is consistent with existing conventions).

## Task list

- [x] Move `BATCH_SIZE`, `BATCH_PAUSE_SECONDS`, and the batch-loop logic from
      `run_screener.py` into `screener_service.py` as `run_screener_batch()`
      (pure orchestration, no DB write — returns rows+failures+run_at)
- [x] Update `run_screener.py`'s `main()` to call `run_screener_batch()` then
      `save_screener_run()`, keep its terminal logging
- [x] Add `POST /api/screener/refresh` route: calls `run_screener_batch()`,
      `save_screener_run()`, returns `ScreenerRefreshResponse`
- [x] Add `ScreenerRefreshResponse`/`ScreenerRefreshFailureSchema` to
      `api/schemas/screener.py`
- [x] Contract amendment (v-bump) in `docs/api-contract.md` documenting
      `POST /api/screener/refresh`
- [x] Add `postScreenerRefresh()` to `ui/src/api/screener.js` + typedefs in
      `ui/src/api/types.js`
- [x] Create `ScreenerRefreshButton.jsx` (accepts a `label` prop: "Refresh" /
      "Run screener"), wire into `ScreenerPage.jsx`'s header and into
      `ScreenerEmptyState.jsx` (replacing its terminal instruction)
- [x] Backend test: `run_screener_batch()` / route-level test with a fake
      provider (partial failure case included) — 3 new tests, full backend
      suite green (246 passed); frontend vitest suite green (43 passed)
- [x] Manual test (real API + UI, via Chrome, against the real 143-ticker
      screener_stocks.txt and live yfinance): clicked "Refresh" on the
      populated page, confirmed disabled/"Refreshing…" state throughout the
      ~2-minute run, then "143 updated · SQ failed" inline warn notice (SQ
      is a real dead/renamed ticker in the universe file — genuine partial
      failure, not a test artifact), "Last screened Just now", and visibly
      updated prices (e.g. AAPL $311.68→$309.90) confirming a live refetch
      rather than a cached replay. **Not separately exercised**: the
      never-run empty-state ("Run screener" label) — verifying it live would
      have required truncating the real screener_results cache, which was
      denied as a destructive local-DB action outside this task's scope;
      it renders the same `ScreenerRefreshButton` already verified above, so
      risk is low, but it's unverified by direct observation.
- [x] Check off Phase 15 in `docs/plan.md` (add the phase entry there too)

## Resolved

- `ScreenerEmptyState.jsx` ("No screen yet" panel, shown when `runAt === null`)
  currently tells you to run `scripts/run_screener.py` from the terminal, with
  no button, because the page couldn't trigger anything itself — that's now
  stale. It gets the same `ScreenerRefreshButton` in place of the terminal
  instruction (comment on the component noting it never triggers the batch
  itself is removed too).
- `run_screener_batch()` takes only `provider` and reads
  `screener_stocks.txt` itself via `read_screener_universe()` — no ticker-list
  injection. The button does exactly what the terminal script does, just
  from the UI.
