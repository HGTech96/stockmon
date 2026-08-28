from datetime import date, timedelta
from decimal import Decimal

from stockmon.api.dependencies import get_market_data_provider
from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.db.models import Trade
from stockmon.main import app
from tests.conftest import make_daily_prices, make_stock

DASHBOARD_META_KEYS = {"dataAsOf", "isStale", "staleMessage"}
DASHBOARD_ROW_KEYS = {
    "ticker", "companyName", "currentPrice", "change1dPct", "status", "suggestion", "warning", "position",
}
DASHBOARD_TOP_KEYS = {"meta", "summary", "money", "stocks"}

DETAIL_TOP_KEYS = {
    "meta", "ticker", "companyName", "currentPrice", "change1dPct", "status",
    "daysOfHistoryAvailable", "daysOfHistoryRequired", "tradingDaysUntilReady",
    "suggestion", "warning", "chart", "indicators", "position", "analysis", "newsLinks",
}
SUGGESTION_KEYS = {"label", "type", "metCount", "totalCount", "checklist", "note"}
CHECKLIST_ITEM_KEYS = {"id", "text", "passed"}
INDICATORS_KEYS = {
    "currentPrice", "change1dPct", "change7dPct", "thirtyDayAverage", "thirtyDayHigh", "thirtyDayLow",
    "distanceFromHighPct", "distanceFromLowPct", "rsi", "todaysVolume", "averageVolume", "volumeVsAveragePct",
}
DETAIL_POSITION_KEYS = {
    "sharesHeld", "avgPurchasePrice", "amountInvested", "currentValue", "profitLoss", "profitLossPct", "profitTarget",
}
PROFIT_TARGET_KEYS = {"targetDollars", "progressDollars", "remainingDollars", "reached"}
NEWS_LINKS_KEYS = {"cnnFinance", "yahooFinance", "googleFinance", "investorRelations"}


def test_dashboard_empty_watchlist(client) -> None:
    r = client.get("/api/stocks")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == DASHBOARD_TOP_KEYS
    assert set(body["meta"].keys()) == DASHBOARD_META_KEYS
    assert body["summary"] is None
    assert body["money"] is None
    assert body["stocks"] == []


def test_dashboard_money_present_with_deposit_only_and_no_trades(client, db) -> None:
    """summary is null with no trades, but money is a SIBLING field, present
    whenever there's any cash activity at all -- a deposit with zero trades
    is a valid state that must still show its cash figures."""
    client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"})

    body = client.get("/api/stocks").json()

    assert body["summary"] is None
    assert body["money"] == {
        "cashAvailable": 100.0,
        "netDeposited": 100.0,
        "realizedEarned": 0.0,
        "realizedLost": 0.0,
        "unrealizedGainOpen": 0.0,
        "unrealizedLossOpen": 0.0,
    }


def test_dashboard_row_shape_and_sort_order(client, db) -> None:
    sell_stock = make_stock(db, "TSLA", "Tesla, Inc.")
    make_daily_prices(db, sell_stock, ["100.00"] * 29 + ["70.00"])  # sharp 1d drop -> warning

    buy_stock = make_stock(db, "AAPL", "Apple Inc.")
    closes = ["120.00"] * 20 + [str(120 - i) for i in range(1, 11)]
    make_daily_prices(db, buy_stock, closes, volumes=[1000] * 29 + [5_000_000])

    insufficient_stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.")
    make_daily_prices(db, insufficient_stock, ["13.00", "13.42"])

    r = client.get("/api/stocks")
    body = r.json()
    tickers = [row["ticker"] for row in body["stocks"]]
    assert tickers[-1] == "RIVN"  # insufficient-history always sorts last

    for row in body["stocks"]:
        assert set(row.keys()) == DASHBOARD_ROW_KEYS

    rivn_row = next(row for row in body["stocks"] if row["ticker"] == "RIVN")
    assert rivn_row["status"] == "insufficient_history"
    assert rivn_row["suggestion"] is None
    assert rivn_row["warning"] is None
    assert rivn_row["position"] is None


def test_dashboard_position_present_for_owned_stock(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["120.00"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)))
    db.commit()

    body = client.get("/api/stocks").json()
    row = body["stocks"][0]
    assert row["position"] == {"profitLoss": 200.0, "profitLossPct": 20.0}
    assert body["summary"] == {
        "totalInvested": 1000.0,
        "totalCurrentValue": 1200.0,
        "totalProfitLoss": 200.0,
        "totalProfitLossPct": 20.0,
    }
    assert body["money"]["unrealizedGainOpen"] == 200.0
    assert body["money"]["unrealizedLossOpen"] == 0.0


def test_detail_ok_status_full_shape(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.", investor_relations_url="https://investor.apple.com")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["90.00"])

    r = client.get("/api/stocks/AAPL")
    assert r.status_code == 200
    body = r.json()

    assert set(body.keys()) == DETAIL_TOP_KEYS
    assert body["status"] == "ok"
    assert body["tradingDaysUntilReady"] is None
    assert body["daysOfHistoryRequired"] == 30
    assert body["daysOfHistoryAvailable"] == 30

    assert set(body["suggestion"].keys()) == SUGGESTION_KEYS
    for item in body["suggestion"]["checklist"]:
        assert set(item.keys()) == CHECKLIST_ITEM_KEYS
    assert body["suggestion"]["metCount"] == sum(1 for c in body["suggestion"]["checklist"] if c["passed"])
    assert body["suggestion"]["totalCount"] == len(body["suggestion"]["checklist"])

    assert set(body["indicators"].keys()) == INDICATORS_KEYS
    assert len(body["chart"]["days"]) == 30
    assert body["chart"]["userAvgPurchasePrice"] is None
    assert body["position"] is None
    assert body["analysis"] is None
    assert set(body["newsLinks"].keys()) == NEWS_LINKS_KEYS
    assert body["newsLinks"]["investorRelations"] == "https://investor.apple.com"
    assert body["newsLinks"]["yahooFinance"] == "https://finance.yahoo.com/quote/AAPL"


def test_detail_insufficient_history(client, db) -> None:
    make_stock(db, "RIVN", "Rivian Automotive, Inc.")

    r = client.get("/api/stocks/RIVN")
    body = r.json()
    assert body["status"] == "insufficient_history"
    assert body["suggestion"] is None
    assert body["indicators"] is None
    assert body["chart"] is None
    assert body["daysOfHistoryRequired"] == 30
    assert body["daysOfHistoryAvailable"] == 0
    assert body["tradingDaysUntilReady"] == 30


def test_detail_owned_position_includes_profit_target(client, db) -> None:
    stock = make_stock(db, "NVDA", "NVIDIA Corporation")
    make_daily_prices(db, stock, ["80.00"] * 29 + ["128.55"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(25), price_per_share=Decimal("88.10"), trade_date=date(2026, 1, 1)))
    db.commit()

    body = client.get("/api/stocks/NVDA").json()
    assert set(body["position"].keys()) == DETAIL_POSITION_KEYS
    assert set(body["position"]["profitTarget"].keys()) == PROFIT_TARGET_KEYS
    assert body["chart"]["userAvgPurchasePrice"] == 88.1


def test_detail_unknown_ticker_is_404(client) -> None:
    r = client.get("/api/stocks/ZZZZ")
    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}


def test_put_analysis_sets_value_and_returns_it(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    r = client.put("/api/stocks/AAPL/analysis", json={"date": "2026-08-20", "value": 210.00})

    assert r.status_code == 200
    assert r.json() == {"date": "2026-08-20", "value": 210.0}

    # No price history yet -- progress can't be computed.
    detail = client.get("/api/stocks/AAPL").json()
    assert detail["analysis"] == {"date": "2026-08-20", "value": 210.0, "progress": None}


def test_analysis_progress_below_target(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["90.00"])

    client.put("/api/stocks/AAPL/analysis", json={"date": "2026-08-20", "value": 120.00})

    detail = client.get("/api/stocks/AAPL").json()
    assert detail["analysis"] == {
        "date": "2026-08-20",
        "value": 120.0,
        "progress": {"targetPrice": 120.0, "progressPrice": 90.0, "remainingPrice": 30.0, "reached": False},
    }


def test_analysis_progress_reached_when_price_at_or_above_target(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["150.00"])

    client.put("/api/stocks/AAPL/analysis", json={"date": "2026-08-20", "value": 120.00})

    detail = client.get("/api/stocks/AAPL").json()
    assert detail["analysis"]["progress"] == {
        "targetPrice": 120.0,
        "progressPrice": 120.0,  # capped at target for a 0-100% bar
        "remainingPrice": 0.0,
        "reached": True,
    }


def test_put_analysis_overwrites_existing_value(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    client.put("/api/stocks/AAPL/analysis", json={"date": "2026-08-20", "value": 210.00})

    r = client.put("/api/stocks/AAPL/analysis", json={"date": "2026-08-25", "value": 225.50})

    assert r.json() == {"date": "2026-08-25", "value": 225.5}


def test_put_analysis_unknown_ticker_is_404(client) -> None:
    r = client.put("/api/stocks/ZZZZ/analysis", json={"date": "2026-08-20", "value": 210.00})
    assert r.status_code == 404


def test_delete_analysis_clears_value(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    client.put("/api/stocks/AAPL/analysis", json={"date": "2026-08-20", "value": 210.00})

    r = client.delete("/api/stocks/AAPL/analysis")

    assert r.status_code == 204
    detail = client.get("/api/stocks/AAPL").json()
    assert detail["analysis"] is None


def test_delete_analysis_unknown_ticker_is_404(client) -> None:
    r = client.delete("/api/stocks/ZZZZ/analysis")
    assert r.status_code == 404


class FakeProvider(MarketDataProvider):
    def __init__(self, company_name: str | None, bars: list[DailyBar] | None = None):
        self._company_name = company_name
        self._bars = bars

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if self._bars is None:
            raise MarketDataError(f"no price history returned for {ticker}")
        return self._bars

    def fetch_current_quote(self, ticker: str) -> Quote:
        raise NotImplementedError

    def fetch_company_name(self, ticker: str) -> str:
        if self._company_name is None:
            raise MarketDataError(f"no company name available for {ticker}")
        return self._company_name

    def fetch_exchange(self, ticker: str) -> str | None:
        return None


def _bar() -> DailyBar:
    return DailyBar(
        date=date(2026, 8, 18),
        open=Decimal("10.00"),
        high=Decimal("11.00"),
        low=Decimal("9.00"),
        close=Decimal("10.50"),
        volume=1000,
    )


def _override_provider(provider: MarketDataProvider) -> None:
    app.dependency_overrides[get_market_data_provider] = lambda: provider


def test_add_stock_valid_ticker_returns_201(client) -> None:
    _override_provider(FakeProvider(company_name="Palantir Technologies Inc.", bars=[_bar()]))
    try:
        r = client.post("/api/stocks", json={"ticker": "pltr"})
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 201
    body = r.json()
    assert set(body.keys()) == {"ticker", "companyName", "historyFetched"}
    assert body == {"ticker": "PLTR", "companyName": "Palantir Technologies Inc.", "historyFetched": True}

    dashboard = client.get("/api/stocks").json()
    assert any(row["ticker"] == "PLTR" for row in dashboard["stocks"])


def test_add_stock_unknown_ticker_is_422(client) -> None:
    _override_provider(FakeProvider(company_name=None))
    try:
        r = client.post("/api/stocks", json={"ticker": "ZZZZ"})
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 422
    assert r.json() == {"error": "Unknown ticker — check the symbol."}


def test_add_stock_already_on_watchlist_is_409(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    _override_provider(FakeProvider(company_name="Apple Inc.", bars=[_bar()]))
    try:
        r = client.post("/api/stocks", json={"ticker": "AAPL"})
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 409
    assert r.json() == {"error": "AAPL is already on your watchlist."}
