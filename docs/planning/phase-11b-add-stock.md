# Phase 11b — Add stock to watchlist

Contract amendment already applied to `docs/api-contract.md` (v1.6 → v1.7,
new `POST /api/stocks` section + changelog entry).

## Overview

New watchlist-management endpoint plus dashboard UI to use it. Ticker
resolution and company-name lookup both go through the existing
`MarketDataProvider` ABC (one new interface method), so the rule "market
data access behind the provider interface" holds. Price-history fetch on
add reuses the exact per-ticker logic `POST /api/refresh` already uses —
extracted into a shared function rather than duplicated.

Add-only: no removal/archive endpoint in this phase.

## Files to create/change

```
api/
  src/stockmon/
    core/
      market_data.py          (change: + fetch_company_name abstract method)
    services/
      yfinance_provider.py    (change: implement fetch_company_name)
      refresh_service.py      (change: extract refresh_stock() helper,
                                reused by refresh_all_stocks and the new
                                add-stock flow)
      stock_service.py        (change: + add_stock_to_watchlist(),
                                + UnknownTickerError, + StockAlreadyOnWatchlistError)
    api/
      schemas/
        stock.py               (new: AddStockRequest, AddStockResponse)
      routes/
        stocks.py               (change: + POST /api/stocks route)
    main.py                     (change: + 422/409 exception handlers)
  tests/
    services/
      test_refresh_service.py   (change: cover extracted refresh_stock())
      test_stock_service.py     (change: + add_stock_to_watchlist tests)
    routes/
      test_stocks_route.py      (change: + POST route tests — valid ticker,
                                  unknown ticker 422, duplicate 409)

ui/
  src/
    api/
      stocks.js                 (change: + addStock())
    components/
      toast/
        Toast.jsx                (new: single top-right toast, scoped to
                                   this feature)
        useToast.js               (new: minimal local state hook —
                                   show(message) / auto-dismiss)
    pages/dashboard/
      DashboardPage.jsx          (change: render AddStockButton + modal +
                                   toast host)
      AddStockButton.jsx         (new: matches RefreshButton's raw-Tailwind
                                   styling, sits beside it)
      AddStockModal.jsx          (new: ticker input, inline 422, closes +
                                   toasts on success/409)
```

## Schemas / interfaces

**core/market_data.py** — one new abstract method:

```python
class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]: ...

    @abstractmethod
    def fetch_current_quote(self, ticker: str) -> Quote: ...

    @abstractmethod
    def fetch_company_name(self, ticker: str) -> str:
        """Resolve a ticker to its company name. Raises MarketDataError if
        the ticker can't be resolved -- this IS the "does this ticker
        exist" check for POST /api/stocks."""
```

**yfinance_provider.py**:

```python
def fetch_company_name(self, ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
    except Exception as exc:
        raise MarketDataError(str(exc)) from exc
    name = (info.get("longName") or info.get("shortName") or "").strip()
    if not name:
        raise MarketDataError(f"no company name available for {ticker}")
    return name
```

Guards from review: (a) any raise here is caught by `add_stock_to_watchlist`
and re-raised as `UnknownTickerError` → the registered 422 handler, never a
bare 500. (b) `.strip()` + falsy-check treats a blank/whitespace-only name
(the "technically resolves but dead symbol" case) as unresolved too, not as
a valid add with an empty name.

**refresh_service.py** — extract the per-stock body already inside the loop:

```python
def refresh_stock(
    db: Session, provider: MarketDataProvider, stock: Stock, days: int = DEFAULT_HISTORY_DAYS
) -> RefreshFailure | None:
    """One ticker's fetch+upsert+commit, success=None / failure=RefreshFailure.
    Used by refresh_all_stocks (looped) and add_stock_to_watchlist (single
    call) -- the literal "reuse the refresh service" the plan asked for."""
    try:
        bars = provider.fetch_daily_history(stock.ticker, days)
        upsert_daily_prices(db, stock.id, bars)
        db.commit()
        return None
    except MarketDataError as exc:
        db.rollback()
        return RefreshFailure(ticker=stock.ticker, error=str(exc))


def refresh_all_stocks(db, provider, days=DEFAULT_HISTORY_DAYS) -> RefreshResult:
    refreshed, failed = [], []
    for stock in db.query(Stock).all():
        failure = refresh_stock(db, provider, stock, days)
        (failed if failure else refreshed).append(failure or stock.ticker)
    return RefreshResult(refreshed=refreshed, failed=failed, data_as_of=datetime.now().astimezone())
```

Confirmed: this is the SAME `refresh_stock()` the new add-stock flow calls
below — `refresh_all_stocks` is rewritten to call it in the loop rather than
inlining its own copy, so `POST /api/refresh` and `POST /api/stocks` share
one implementation and can't drift. `test_refresh_service.py`'s existing
partial-failure test keeps passing unmodified against the refactor (same
inputs/outputs at the `refresh_all_stocks` boundary); the new coverage is on
`refresh_stock()` itself and on the add-stock path reusing it.

**services/stock_service.py** — new errors + function:

```python
class UnknownTickerError(Exception):
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__("Unknown ticker — check the symbol.")

class StockAlreadyOnWatchlistError(Exception):
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__(f"{ticker} is already on your watchlist.")

@dataclass(frozen=True)
class AddStockResult:
    stock: Stock
    history_fetched: bool  # False = name resolved but the immediate history
                            # fetch failed; stock is still added (see below)

def add_stock_to_watchlist(db: Session, provider: MarketDataProvider, ticker: str) -> AddStockResult:
    """Two independent failure modes, per review:
    - name doesn't resolve (raises, or resolves blank) -> reject, nothing
      stored (UnknownTickerError -> 422).
    - name resolves but history fetch fails -> still add the stock; it's a
      real ticker, the history gap is transient and self-heals on the next
      refresh. Caller uses `history_fetched` to word the success message
      honestly instead of implying the row has data already."""
    ticker = ticker.strip().upper()
    if db.query(Stock).filter(Stock.ticker == ticker).first() is not None:
        raise StockAlreadyOnWatchlistError(ticker)

    try:
        company_name = provider.fetch_company_name(ticker)
    except MarketDataError as exc:
        raise UnknownTickerError(ticker) from exc

    stock = Stock(ticker=ticker, company_name=company_name)
    db.add(stock)
    db.commit()
    db.refresh(stock)

    failure = refresh_stock(db, provider, stock)
    return AddStockResult(stock=stock, history_fetched=failure is None)
```

**api/schemas/stock.py**:

```python
class AddStockRequest(CamelModel):
    ticker: str

class AddStockResponse(CamelModel):
    ticker: str
    company_name: str
    history_fetched: bool

    @classmethod
    def from_core(cls, result: AddStockResult) -> "AddStockResponse":
        return cls(
            ticker=result.stock.ticker,
            company_name=result.stock.company_name,
            history_fetched=result.history_fetched,
        )
```

**api/routes/stocks.py** — add:

```python
@router.post("/api/stocks", response_model=AddStockResponse, status_code=201)
def add_stock(
    body: AddStockRequest,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> AddStockResponse:
    result = add_stock_to_watchlist(db, provider, body.ticker)
    return AddStockResponse.from_core(result)
```

(`get_market_data_provider` currently lives in `refresh.py`; move it to a
shared spot — simplest: import it from `refresh.py` into `stocks.py`, or
lift it into `market_data.py`/a small `dependencies.py`. Decide during
implementation, not a contract concern.)

**main.py** — two new handlers:

```python
@app.exception_handler(UnknownTickerError)
def handle_unknown_ticker_error(request, exc) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": str(exc)})

@app.exception_handler(StockAlreadyOnWatchlistError)
def handle_stock_already_exists_error(request, exc) -> JSONResponse:
    return JSONResponse(status_code=409, content={"error": str(exc)})
```

**ui/src/api/client.js** — the shared `request()` throws a plain `Error`
with only `.message`; the modal needs to tell 409 (toast) apart from 422
(inline). Attach status to the thrown error:

```js
if (!res.ok) {
  const err = new Error(body.error ?? "Request failed");
  err.status = res.status;
  throw err;
}
```

**ui/src/api/stocks.js** — add:

```js
export function addStock(ticker) {
  return request("/stocks", { method: "POST", body: JSON.stringify({ ticker }) });
}
```

**Toast** — minimal, scoped to this feature only (per plan: "do not
retrofit toasts elsewhere"):

```jsx
// components/toast/useToast.js
export function useToast() {
  const [message, setMessage] = useState(null);
  function show(msg) {
    setMessage(msg);
    setTimeout(() => setMessage(null), 4000);
  }
  return { message, show };
}

// components/toast/Toast.jsx
export function Toast({ message }) {
  if (!message) return null;
  return (
    <div className="fixed top-5 right-5 z-50 rounded-lg border border-good-border bg-good-bg px-4 py-2.5 text-[13px] font-medium text-good shadow-pop">
      {message}
    </div>
  );
}
```

`DashboardPage` owns the `useToast()` instance, renders `<Toast/>` once,
and passes `show` down to `AddStockModal`.

**AddStockModal mutation** — `err.status` (added to `client.js`, see above)
distinguishes 409 (toast + close) from 422 (stays open, renders inline);
success wording depends on `historyFetched`, per review:

```js
const mutation = useMutation({
  mutationFn: (ticker) => addStock(ticker),
  onSuccess: (data) => {
    queryClient.invalidateQueries({ queryKey: ["stocks"] });
    onClose();
    showToast(
      data.historyFetched
        ? `${data.ticker} added to your watchlist.`
        : `${data.ticker} added — price data will load on the next refresh.`
    );
  },
  onError: (err) => {
    if (err.status === 409) {
      onClose();
      showToast(err.message); // "<TICKER> is already on your watchlist." — verbatim from the backend
    }
    // 422: no-op here — mutation.error renders inline in the JSX below, modal stays open
  },
});
```

## Task list

Backend
- [x] `core/market_data.py`: add `fetch_company_name` abstract method
- [x] `yfinance_provider.py`: implement `fetch_company_name`
- [x] `refresh_service.py`: extract `refresh_stock()`, reuse in `refresh_all_stocks`
- [x] `stock_service.py`: add `UnknownTickerError`, `StockAlreadyOnWatchlistError`, `add_stock_to_watchlist()`
- [x] `api/schemas/stock.py`: `AddStockRequest` / `AddStockResponse`
- [x] `api/routes/stocks.py`: `POST /api/stocks`
- [x] `main.py`: register the two new exception handlers
- [x] Tests: `refresh_service` (extracted helper still covers partial-failure case), `stock_service` (valid ticker incl. history stored, unknown ticker, duplicate — case-insensitive dup check), `stocks_route` (201 shape, 422 shape, 409 shape) — 216 backend tests pass

UI
- [x] `client.js`: attach `.status` to thrown errors
- [x] `api/stocks.js`: `addStock()`
- [x] `components/toast/`: `useToast`, `Toast` (tone: good/neutral)
- [x] `pages/dashboard/AddStockButton.jsx`
- [x] `pages/dashboard/AddStockModal.jsx` (uppercase input, non-empty guard, 422 inline, 409 → close + toast, success → close + toast worded from `historyFetched` + invalidate `["stocks"]`)
- [x] `DashboardPage.jsx`: wire button + modal + toast host next to `RefreshButton`
- [x] Manual check (via Chrome, against a real API+DB instance): added a real ticker (PLTR) and confirmed it appeared with live data + green success toast; added an unknown ticker (ZZZZZZ) and confirmed the inline 422 with the modal staying open; added a duplicate (AAPL) and confirmed the gray toast + modal closing. Test row removed from the dev DB afterward (add-only endpoint, no in-app removal).

Implementation note: `get_market_data_provider` was moved out of `refresh.py`
into a new shared `api/dependencies.py` (resolves the plan's one open
question), imported by both `refresh.py` and `stocks.py`.

## Open questions

Resolved by review:
- Name-resolution failure → reject (422), nothing stored. History-fetch
  failure after a good name → add anyway, `historyFetched: false`, honest
  toast wording. See `AddStockResult`/`AddStockResponse` above.
- `refresh_all_stocks` confirmed to call the shared `refresh_stock()`
  rather than keep its own copy.

Still open:
1. **Where does `get_market_data_provider` live** — leave it in
   `refresh.py` and import into `stocks.py`, or move it somewhere shared?
   No behavior difference, just tidiness.
