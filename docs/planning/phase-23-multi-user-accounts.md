# Phase 23 — Multi-user accounts

## ✅ CLAUDE.md updated

`CLAUDE.md` said "Single local user" and listed auth under "Don't add
... without asking." Both lines are now updated: the app is multiple local,
admin-created users each with their own portfolio, and auth is allowed
scoped to simple session-cookie login — no OAuth/SSO, no roles, no
self-service signup.

## Overview

Today, `stocks`/`trades`/`cash_events`/`settings` are one global set of
tables — effectively one implicit user. This phase adds real accounts
(username + password, session-cookie auth) and splits the data model so
each user has their own watchlist, trades, cash ledger, hard-cap settings,
and analysis notes — while market data (ticker + price history) stays
shared, since it's the same public data for everyone. The screener stays
global/shared (unchanged) per CLAUDE.md's "separate subsystem" framing.

This is big enough to touch nearly every service function, route, and page.
Split into three sub-phases for sequencing, tracked inline in this one file
(no separate per-subphase docs):

- **23a** — `users`/`sessions` tables, password hashing, login/logout/me
  endpoints, `get_current_user` dependency (not yet wired into existing
  routes)
- **23b** — split `stocks` into shared `tickers`+`daily_prices` and a new
  per-user `watchlist_entries`; add `user_id` to `trades` (via
  `watchlist_entries`), `cash_events`, `settings`, `refresh_status`; wire
  `get_current_user` into every existing route/service call
- **23c** — frontend: login page, auth context, protected routes, cookie
  credentials on every request, logout

## Data model changes

```
users                              (new)
  id            PK
  username      str, unique
  email         str, unique, NULLABLE   # not collected yet; room for later
  password_hash str
  created_at    datetime

sessions                           (new)
  id            PK (opaque token, e.g. secrets.token_urlsafe(32))
  user_id       FK users.id
  created_at    datetime
  expires_at    datetime   # fixed 30-day expiry from login, no sliding renewal

tickers                            (renamed from `stocks`; shared)
  id                       PK
  ticker                   str, unique
  company_name             str
  investor_relations_url   str | None
  exchange                 str | None
  created_at               datetime
  # analysis_date/analysis_value MOVE to watchlist_entries (per-user)

daily_prices                       (unchanged shape, FK retargeted)
  ticker_id  FK tickers.id   # was stock_id

watchlist_entries                  (new; "my tracked stock")
  id             PK
  user_id        FK users.id
  ticker_id      FK tickers.id
  analysis_date  date | None
  analysis_value Numeric(12,4) | None
  created_at     datetime
  UNIQUE(user_id, ticker_id)

trades
  watchlist_entry_id  FK watchlist_entries.id   # was stock_id
  action, shares, price_per_share, trade_date, created_at  # unchanged

profit_targets
  watchlist_entry_id  PK, FK watchlist_entries.id   # was stock_id
  target_dollars                                    # unchanged

settings                           (was a singleton row, id=1)
  user_id  PK, FK users.id         # was fixed id=1
  default_profit_target_dollars

cash_events
  + user_id  FK users.id           # new column

refresh_status                     (was a singleton row, id=1)
  user_id  PK, FK users.id         # was fixed id=1
  last_attempted_at, last_succeeded_at, had_failures   # unchanged

screener_stocks.txt / screener_results   # UNCHANGED — stays global
```

`ticker_id` replaces `stock_id` as the FK target everywhere it appears
today. Adding a ticker to your watchlist (Phase 11b's "Add stock" flow)
becomes: find-or-create the shared `Ticker` row, then create your own
`WatchlistEntry` pointing at it — refresh only re-fetches a ticker's price
history if no one has it yet or it's stale, benefiting every user tracking
it.

## API contract impact

Response shapes stay fixed per `docs/api-contract.md`'s rule — no field
renames. What changes:

- New endpoints: `POST /api/auth/login`, `POST /api/auth/logout`,
  `GET /api/auth/me`
- Every existing endpoint now requires a valid session cookie; add a `401`
  response case to each in the contract doc
- No new admin-facing `/register` endpoint (accounts are created via a
  terminal script, mirroring `scripts/run_screener.py`'s manual-job pattern)

## Migration / rollout for existing data

Alembic migrations only create tables/columns and rename FKs — they will
NOT invent a user or guess a password. Rollout order:

1. [x] Ran `scripts/create_user.py` against the real dev DB to create the
   first account (`hgtech`, id=2)
2. [x] Ran migration `a3c7b38e1f11` — verified all 16 pre-existing tickers,
   watchlist entries, trades, and both cash events landed on that
   account; `settings`/`refresh_status` rows created for it
3. From now on, `scripts/create_user.py` can create additional accounts
   with empty portfolios

## Sub-phase breakdown

### 23a — Auth foundation ✅ done
- [x] `users`, `sessions` tables + migration (`UserSession` in code/`sessions`
      table — named to avoid colliding with `sqlalchemy.orm.Session`)
- [x] Password hashing: stdlib `hashlib.pbkdf2_hmac` (SHA-256, random
      per-user salt via `secrets`, 260k iterations) — no new dependency
- [x] `auth_service.py`: `create_user`, `authenticate`, `create_session`,
      `get_user_by_session`, `delete_session`
- [x] `get_current_user` FastAPI dependency in `api/deps.py` (reads session
      cookie, 401 if missing/expired) — defined but not yet required by
      other routes
- [x] `routes/auth.py`: `POST /api/auth/login` (sets httponly/samesite=lax
      cookie), `POST /api/auth/logout` (clears it), `GET /api/auth/me`
- [x] `scripts/create_user.py`
- [x] Contract doc: new `/api/auth/*` section, v1.16
- [x] Tests: `test_auth_service.py` + `test_auth_route.py` (bad password,
      expired/missing/unknown session, login/logout/me happy paths) — full
      suite green (311 passed)
- [x] Manual smoke test against the real dev DB: migration applied, live
      login → cookie → `/me` → logout → `/me` 401, verified via curl

### 23b — Data isolation ✅ done
- [x] Migration `a3c7b38e1f11`: `stocks`→`tickers` rename,
      `watchlist_entries` table (data-migrated from every existing
      ticker's analysis fields), retargeted `daily_prices`/`trades`/
      `profit_targets` FKs, `user_id` added to `cash_events`,
      `settings`→per-user PK, `refresh_status`→per-user PK. Requires one
      user to exist first (raises with a clear message otherwise) and
      assigns all pre-existing rows to that first user — matches the
      rollout order above
- [x] `db/models.py`: `Ticker`, `WatchlistEntry` (new); retargeted FKs on
      `DailyPrice`/`Trade`/`ProfitTarget`; `Settings`/`RefreshStatus` keyed
      by `user_id`; `CashEvent` gains `user_id`
- [x] Every service function (`stock_service`, `stock_detail_service`,
      `dashboard_service`, `portfolio_service`, `trade_service`,
      `cash_service`, `money_service`, `settings_service`,
      `refresh_service`, `import_service`) gains a `user_id` parameter and
      scopes its queries by it; `stock_service.get_watchlist_entry` is the
      one shared ticker→this-user's-entry resolver (404 whether the
      ticker doesn't exist or just isn't this user's)
- [x] Every route in `routes/{stocks,portfolio,trades,cash,settings,
      refresh}.py` takes `current_user: User = Depends(get_current_user)`
      and passes `current_user.id` through. Screener routes deliberately
      untouched (stays global/shared, unauthenticated) — its `meta`
      freshness no longer borrows the now-per-user `refresh_status` table;
      it has its own (`get_screener_freshness`/`get_live_freshness` in
      `freshness_service.py`)
- [x] `core/` unaffected — pure functions never took DB rows, this was
      entirely a services/routes/db change
- [x] `scripts/import_history.py` and `scripts/seed_watchlist.py` take a
      required `<username>` argument
- [x] Tests: every existing service/route test updated to create a user
      fixture and scope through it (`tests/conftest.py`: `make_user`,
      `make_ticker`, `make_stock` now returns a `WatchlistEntry`,
      `authed_client` fixture logs in as the default test user so most
      route tests were otherwise unchanged); added cross-user isolation
      tests across trades, cash, settings, stock detail, import, and the
      dashboard route (full suite: 323 passed)
- [x] `docs/api-contract.md` v1.17: every endpoint but the screener now
      requires auth and is scoped per-user; no response shape changes

### 23c — Frontend auth
- [ ] `ui/src/api/auth.js` (login/logout/me)
- [ ] `ui/src/api/client.js`: `credentials: "include"` on every request;
      on a `401`, let it propagate so the auth layer can redirect
- [ ] `AuthContext` (justified exception to "no context unless
      unavoidable" — this is the unavoidable case) + `useAuth` hook,
      wraps `App.jsx`
- [ ] `LoginPage.jsx` (username/password form, inline 401 error) — no
      register page (admin-created accounts)
- [ ] `ProtectedRoute` wrapper around the existing route tree; redirect to
      `/login` when `me` fails
- [ ] Logout action in `AppShell`/`NavTabs`
- [ ] Manual verification: two accounts, confirm each sees only their own
      watchlist/portfolio/cash/settings/analysis; confirm hard-cap and
      analysis-progress bars reflect the logged-in user's own data

## Resolved decisions

1. `CLAUDE.md` updated (see above).
2. Session lifetime: fixed 30 days from login, no sliding renewal.
3. `users.username` is the login field (plain username); `email` exists as
   a nullable column now for future use, not required at signup.
4. No new dependency — password hashing uses stdlib `hashlib.pbkdf2_hmac`.
   Auth strategy stays a DB-backed session cookie (simplest: no signing-key
   management, revocation is a `DELETE`), not JWT.
5. No sub-phase file split — 23a/23b/23c tracked inline in this file.

## Open questions for you

None outstanding — ready to implement 23a first unless you want changes.
