# Phase 24 — Deployment

## Overview

Ships stockmon to the public internet for the first time: Render (API) +
Vercel or Cloudflare Pages (UI) + Neon (Postgres), all free tier, personal
use. Everything before this phase assumed local-only access; deployment
changes the threat model (public login endpoint, cross-origin cookies,
unauthenticated screener refresh reachable by anyone), so 24a fixes
exactly what the Part 1 audit found — nothing more — before any
infrastructure work happens.

**Architecture — decided:** same-origin proxy. Vercel/Cloudflare Pages
proxies `/api/*` to the Render backend (a rewrite rule, not real CORS), so
the browser sees ONE origin. This keeps today's `SameSite=Lax` cookie
working unchanged — only `Secure=True` needs to become conditional on
environment. No `SameSite=None`, no CORS-with-credentials setup, no CSRF
mitigation needed, since the browser never makes a cross-site request.
Confirmed no timeout conflict: Vercel's external-rewrite proxy timeout is
120s on the free tier, comfortably above Render's cold-start window (see
24d).

No custom domain — the free `*.onrender.com` and `*.vercel.app`/
`*.pages.dev` subdomains are the final answer here, not a placeholder for
a later phase.

## Files to create/change

```
api/src/stockmon/
├── config.py                  (+ ENVIRONMENT setting)
├── api/routes/auth.py         (secure= from config; 429 handling for lockout)
├── services/auth_service.py   (PBKDF2 iteration bump; login-attempt tracking + lockout)
├── services/screener_service.py  (+ MIN_REFRESH_INTERVAL_MINUTES guard)
├── db/models.py               (+ LoginAttempt table)
├── main.py                    (+ exception handler for the lockout error)
api/alembic/versions/
└── <rev>_add_login_attempts.py
api/scripts/
├── reset_to_initial_state.py  (add required <username> arg, scope by user)
└── reset_login_lockout.py     (new — same pattern as create_user.py)
api/pyproject.toml             (fastapi/starlette version bump)
ui/
├── vercel.json  OR  wrangler.toml     (rewrite /api/* -> Render backend)
└── package.json                       (npm audit fix for fast-uri/qs)
docs/
├── api-contract.md            (note the new 429 lockout response)
└── planning/phase-24-deployment.md    (this file)
.env.example                   (document ENVIRONMENT, still placeholders)
```

## Config / schema

**New env var:**

```
ENVIRONMENT=local | production   # drives cookie Secure flag only
```

`UI_ORIGIN` stays as-is for local dev (Vite proxy already makes that
same-origin too) and is not load-bearing in prod under this architecture —
the browser only ever talks to the frontend's own domain, so the FastAPI
`CORSMiddleware` path is never exercised in production traffic.

**Cookie, env-aware** (`routes/auth.py`):

```python
response.set_cookie(
    key=SESSION_COOKIE_NAME,
    value=session.id,
    httponly=True,
    secure=app_settings.environment == "production",
    samesite="lax",
    max_age=int(SESSION_LIFETIME.total_seconds()),
)
```

**Login attempt tracking — DB-backed, decided:**

```python
class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), index=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    succeeded: Mapped[bool] = mapped_column(Boolean)
```

**Lockout rule — pure sliding window, no separate `locked_until` column:**
on every `authenticate()` call, first count `LoginAttempt` rows for that
username with `succeeded = False` and `attempted_at` within the last 15
minutes; if that count is `>= 5`, reject immediately (before even checking
the password) with a new `TooManyAttemptsError` → `429`. Every attempt
(success or failure) is still recorded. Successes do NOT clear prior
failures — the lock simply self-expires as old failures age out of the
15-minute window, so a lock lasts anywhere from a few minutes up to the
full 15, with no extra state to manage. This is the "pick whichever is
simpler" option: one table, one query, no expiry bookkeeping.

`scripts/reset_login_lockout.py <username>` deletes that username's
`LoginAttempt` rows outright (simplest reset — not just the failed ones),
for the rare case you lock yourself out and don't want to wait.

**Screener refresh guard — named constant, decided:**

```python
# screener_service.py, alongside BATCH_SIZE / BATCH_PAUSE_SECONDS
MIN_REFRESH_INTERVAL_MINUTES = 15
```

`run_screener_batch`'s caller (the route) checks the latest
`screener_results.run_at` before running; if under 15 minutes old, reject
(429) instead of starting a new batch. `GET /api/screener` (reading
cached results) is completely unaffected — only the refresh trigger is
guarded.

## 24a — Security hardening

Scoped exactly to the Part 1 audit findings — no extra hardening invented.

- [ ] Cookie `secure` flag driven by a new `ENVIRONMENT` setting
      (`config.py`), `True` only when `ENVIRONMENT=production`; `samesite`
      stays `"lax"` (same-origin proxy architecture, decided)
- [ ] `login_attempts` table + migration; `authenticate()` records every
      attempt and enforces the 15-minute / 5-attempt sliding-window
      lockout described above; new `TooManyAttemptsError` → `429` handler
      in `main.py`
- [ ] `scripts/reset_login_lockout.py` (new, mirrors `create_user.py`'s
      shape: prompt/arg for username, clear that user's `login_attempts`
      rows, print confirmation)
- [ ] `_PBKDF2_ITERATIONS` raised to 600,000 (`auth_service.py`) —
      existing hashes keep working since the count travels with each
      stored hash, no migration/rehash needed
- [ ] `MIN_REFRESH_INTERVAL_MINUTES = 15` guard on
      `POST /api/screener/refresh`, checked against the latest
      `screener_results.run_at`; `GET /api/screener` unaffected
- [ ] `fastapi`/`starlette` bumped to current releases; run the full test
      suite after, skim changelogs for anything security-relevant
- [ ] `npm audit fix` in `ui/` for `fast-uri`/`qs` (dev-only transitive
      deps of `shadcn`, but the fix is free)
- [ ] `scripts/reset_to_initial_state.py`: add a required `<username>` arg
      and scope both deletes by that user's `id` (currently wipes every
      user's trades/cash — pre-dates Phase 23b, found during this audit,
      not web-exposed but a real local data-safety trap now)
- [ ] Confirm the prod start command runs `uvicorn stockmon.main:app`
      directly (no `--reload`, no dev entrypoint)

## 24b — Config for prod

| Var | Local (`.env`) | Prod (Render/Vercel/Neon) | Notes |
|---|---|---|---|
| `DATABASE_URL` | local Postgres | Neon connection string | Neon requires `sslmode=require` — confirm `psycopg` picks it up from the URL |
| `TEST_DATABASE_URL` | local Postgres | not set in prod | test-only, never needed outside `pytest` |
| `UI_ORIGIN` | `http://localhost:5173` | unchanged / unused | not load-bearing in prod under the same-origin-proxy architecture |
| `ENVIRONMENT` | `local` (or unset) | `production` | new — drives cookie `Secure` only |

- [ ] Render: set `DATABASE_URL` (Neon), `ENVIRONMENT=production`, start
      command `uvicorn stockmon.main:app --host 0.0.0.0 --port $PORT`
- [ ] Vercel/Cloudflare Pages: set the `/api/*` rewrite rule to the Render
      backend URL
- [ ] `.env.example` updated with `ENVIRONMENT` (placeholder/comment only,
      as today)
- [ ] Confirm no other code path reads `os.environ` directly outside
      `config.py`'s `Settings` class (single source of truth)

## 24c — Neon migration

Data-layer only — no schema or business-logic changes.

- [ ] Create Neon project + database; grab its connection string
- [ ] Point `DATABASE_URL` at Neon (locally first, as a dry run)
- [ ] Run `alembic upgrade head` against Neon from a clean database —
      confirm every migration in `api/alembic/versions/` applies in order,
      including the data-migrating `a3c7b38e1f11` (needs a user row to
      exist first — run `scripts/create_user.py` against Neon before it,
      same rollout order as the original Phase 23b run)
- [ ] `scripts/create_user.py` against Neon for the real production account(s)
- [ ] Spot-check: connect with `psql`, confirm table shapes match local
- [ ] No application code changes in this sub-phase — if any are needed,
      that's a sign 24a/24b missed something, not a 24c task

## 24d — Deploy

- [ ] Render: connect the GitHub repo, root directory `api/`, build +
      start commands, free tier
- [ ] Vercel or Cloudflare Pages: connect the GitHub repo, root directory
      `ui/`, build command `npm run build`, output `dist/`, free tier
- [ ] Wire the `/api/*` rewrite (Vercel `vercel.json` `rewrites`, or
      Cloudflare Pages `_redirects`/Functions) to the Render backend URL
- [ ] **Known tradeoff, not a bug**: Render free tier cold-starts after
      ~15 min idle — first request after a gap takes ~30-60s. Confirmed
      the chosen proxy's own timeout (120s on Vercel's free tier) comfortably
      covers this, so it surfaces as a slow first load, not a proxy error.
      Documented here so it's not mistaken for a broken deploy during
      verification

## 24e — Verification (run after deploy, before calling this phase done)

- [ ] Log in from a phone on **cellular data**, not home wifi — confirms
      the proxy/cookie setup actually works outside a same-network dev
      assumption
- [ ] `POST /api/refresh` pulls live prices in prod
- [ ] Record a trade end-to-end (buy + sell), confirm position math and
      cash balance match what local dev would produce
- [ ] Reload the page — session persists (cookie survives a hard refresh)
- [ ] Trigger the login lockout deliberately (5 wrong passwords), confirm
      the 429 and that `scripts/reset_login_lockout.py` clears it against Neon
- [ ] Confirm `POST /api/screener/refresh` correctly refuses a second call
      within 15 minutes of the first, in prod
- [ ] Confirm a second, freshly-created account sees an empty
      watchlist/portfolio in prod (per-user isolation, same check as
      Phase 23's local verification, now against Neon)
- [ ] Screener page loads and its "Refresh" completes within Render's
      request timeout

## Resolved decisions

1. Same-origin proxy (Vercel/Cloudflare Pages → Render), not separate
   origins. `SameSite=Lax` unchanged, no CORS-with-credentials, no CSRF
   work. Vercel free-tier rewrite timeout (120s) confirmed to exceed
   Render's cold-start window.
2. Lockout is DB-backed (`login_attempts` table): 5 failed attempts / 15
   minutes, pure sliding window (no separate lock-expiry state).
   `scripts/reset_login_lockout.py` added for manual clearing.
3. Screener-refresh guard is a minimum-interval check (15 minutes) against
   `screener_results.run_at`, via a named constant
   (`MIN_REFRESH_INTERVAL_MINUTES`) next to the existing batch constants.
4. No custom domain — free subdomains only, permanently, not a later phase.

## Open questions for you

None outstanding — ready to implement 24a first unless you want changes.
