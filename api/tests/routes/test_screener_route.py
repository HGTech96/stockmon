from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from stockmon.api.dependencies import get_market_data_provider
from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.db.models import ScreenerResult
from stockmon.main import app
from stockmon.services import screener_service

SCREENER_TOP_KEYS = {"meta", "runAt", "results"}
SCREENER_RESULT_KEYS = {
    "ticker", "companyName", "currentPrice", "change1dPct", "suggestion",
    "metCount", "totalCount", "rsi", "priceVs30dAvgPct", "sharpMove", "status",
}
REFRESH_TOP_KEYS = {"refreshed", "failed", "runAt"}


class FakeProvider(MarketDataProvider):
    def __init__(self, history_by_ticker: dict[str, list[DailyBar]], failing_history_tickers: set[str] | None = None):
        self._history_by_ticker = history_by_ticker
        self._failing_history_tickers = failing_history_tickers or set()

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if ticker in self._failing_history_tickers:
            raise MarketDataError(f"download timeout for {ticker}")
        return self._history_by_ticker[ticker]

    def fetch_current_quote(self, ticker: str) -> Quote:
        raise NotImplementedError

    def fetch_company_name(self, ticker: str) -> str:
        return f"{ticker} Inc."

    def fetch_exchange(self, ticker: str) -> str | None:
        return None


def _bars(n: int, *, start: date = date(2026, 1, 1)) -> list[DailyBar]:
    return [
        DailyBar(date=start + timedelta(days=i), open=Decimal(100), high=Decimal(100), low=Decimal(100), close=Decimal(100), volume=1_000_000)
        for i in range(n)
    ]


def test_screener_never_run_is_empty_state(client) -> None:
    r = client.get("/api/screener")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == SCREENER_TOP_KEYS
    assert body["runAt"] is None
    assert body["results"] == []


def test_screener_returns_latest_run_rows(client, db) -> None:
    run_at = datetime(2026, 8, 19, 9, 12, tzinfo=timezone.utc)
    db.add(
        ScreenerResult(
            ticker="PLTR",
            company_name="Palantir Technologies Inc.",
            current_price=Decimal("27.85"),
            change_1d_pct=Decimal("1.52"),
            status="ok",
            suggestion="BUY",
            conditions_met=3,
            conditions_total=4,
            rsi=Decimal("38.00"),
            price_vs_30d_avg_pct=Decimal("-4.10"),
            sharp_move=False,
            run_at=run_at,
        )
    )
    db.commit()

    r = client.get("/api/screener")
    assert r.status_code == 200
    body = r.json()
    assert body["runAt"] is not None
    assert len(body["results"]) == 1

    row = body["results"][0]
    assert set(row.keys()) == SCREENER_RESULT_KEYS
    assert row["ticker"] == "PLTR"
    assert row["companyName"] == "Palantir Technologies Inc."
    assert row["currentPrice"] == 27.85
    assert row["change1dPct"] == 1.52
    assert row["suggestion"] == "BUY"
    assert row["metCount"] == 3
    assert row["totalCount"] == 4
    assert row["rsi"] == 38.0
    assert row["priceVs30dAvgPct"] == -4.1
    assert row["sharpMove"] is False
    assert row["status"] == "ok"


def test_screener_insufficient_history_row_has_null_indicators(client, db) -> None:
    run_at = datetime(2026, 8, 19, 9, 12, tzinfo=timezone.utc)
    db.add(
        ScreenerResult(
            ticker="NEWCO",
            company_name="Newco Inc.",
            current_price=Decimal("5.00"),
            change_1d_pct=Decimal("0.00"),
            status="insufficient_history",
            suggestion=None,
            conditions_met=None,
            conditions_total=None,
            rsi=None,
            price_vs_30d_avg_pct=None,
            sharp_move=None,
            run_at=run_at,
        )
    )
    db.commit()

    body = client.get("/api/screener").json()
    row = body["results"][0]
    assert row["status"] == "insufficient_history"
    assert row["suggestion"] is None
    assert row["rsi"] is None
    assert row["sharpMove"] is None


def test_post_screener_refresh_populates_cache_and_reports_failures(client, db, monkeypatch) -> None:
    monkeypatch.setattr(screener_service, "read_screener_universe", lambda: ["AAA", "BBB"])
    provider = FakeProvider(history_by_ticker={"AAA": _bars(30)}, failing_history_tickers={"BBB"})
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    try:
        r = client.post("/api/screener/refresh")
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == REFRESH_TOP_KEYS
    assert body["refreshed"] == ["AAA"]
    assert body["failed"] == [{"ticker": "BBB", "error": "download timeout for BBB"}]
    assert body["runAt"] is not None

    cached = client.get("/api/screener").json()
    assert cached["runAt"] is not None
    assert [row["ticker"] for row in cached["results"]] == ["AAA"]


def test_post_screener_refresh_replaces_previous_run(client, db, monkeypatch) -> None:
    db.add(
        ScreenerResult(
            ticker="OLD",
            company_name="Old Inc.",
            current_price=Decimal("1.00"),
            change_1d_pct=Decimal("0.00"),
            status="ok",
            suggestion="WAIT",
            conditions_met=1,
            conditions_total=4,
            rsi=Decimal("50.00"),
            price_vs_30d_avg_pct=Decimal("0.00"),
            sharp_move=False,
            run_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        )
    )
    db.commit()

    monkeypatch.setattr(screener_service, "read_screener_universe", lambda: ["NEW"])
    provider = FakeProvider(history_by_ticker={"NEW": _bars(30)})
    app.dependency_overrides[get_market_data_provider] = lambda: provider

    try:
        r = client.post("/api/screener/refresh")
    finally:
        del app.dependency_overrides[get_market_data_provider]

    assert r.status_code == 200
    cached = client.get("/api/screener").json()
    assert [row["ticker"] for row in cached["results"]] == ["NEW"]
