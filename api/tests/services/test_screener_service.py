from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote
from stockmon.core.screener import ScreenerEvaluation
from stockmon.db.models import ScreenerResult
from stockmon.services import screener_service
from stockmon.services.screener_service import (
    ScreenerFetchFailure,
    ScreenerRow,
    fetch_and_evaluate_ticker,
    get_latest_screener_run,
    run_screener_batch,
    save_screener_run,
)


class FakeProvider(MarketDataProvider):
    def __init__(
        self,
        history_by_ticker: dict[str, list[DailyBar]],
        failing_history_tickers: set[str] | None = None,
        failing_name_tickers: set[str] | None = None,
    ):
        self._history_by_ticker = history_by_ticker
        self._failing_history_tickers = failing_history_tickers or set()
        self._failing_name_tickers = failing_name_tickers or set()

    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        if ticker in self._failing_history_tickers:
            raise MarketDataError(f"download timeout for {ticker}")
        return self._history_by_ticker[ticker]

    def fetch_current_quote(self, ticker: str) -> Quote:
        raise NotImplementedError

    def fetch_company_name(self, ticker: str) -> str:
        if ticker in self._failing_name_tickers:
            raise MarketDataError(f"no name for {ticker}")
        return f"{ticker} Inc."

    def fetch_exchange(self, ticker: str) -> str | None:
        return None


def _bars(n: int, *, start: date = date(2026, 1, 1)) -> list[DailyBar]:
    return [
        DailyBar(
            date=start + timedelta(days=i),
            open=Decimal(100),
            high=Decimal(100),
            low=Decimal(100),
            close=Decimal(100),
            volume=1_000_000,
        )
        for i in range(n)
    ]


def test_fetch_and_evaluate_ticker_success() -> None:
    provider = FakeProvider(history_by_ticker={"PLTR": _bars(30)})
    result = fetch_and_evaluate_ticker(provider, "PLTR")

    assert isinstance(result, ScreenerRow)
    assert result.ticker == "PLTR"
    assert result.company_name == "PLTR Inc."
    assert result.evaluation.status == "ok"


def test_fetch_and_evaluate_ticker_history_failure_is_skipped() -> None:
    provider = FakeProvider(history_by_ticker={}, failing_history_tickers={"XYZ"})
    result = fetch_and_evaluate_ticker(provider, "XYZ")

    assert isinstance(result, ScreenerFetchFailure)
    assert result.ticker == "XYZ"
    assert result.error == "download timeout for XYZ"


def test_fetch_and_evaluate_ticker_name_failure_falls_back_to_symbol() -> None:
    provider = FakeProvider(history_by_ticker={"NEWCO": _bars(30)}, failing_name_tickers={"NEWCO"})
    result = fetch_and_evaluate_ticker(provider, "NEWCO")

    assert isinstance(result, ScreenerRow)
    assert result.company_name == "NEWCO"
    assert result.evaluation.status == "ok"


def test_save_screener_run_truncates_and_rewrites(db) -> None:
    run_at_1 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    row_1 = ScreenerRow(
        ticker="AAA",
        company_name="AAA Inc.",
        evaluation=ScreenerEvaluation(
            status="ok", current_price=Decimal(10), change_1d_pct=Decimal(1),
            suggestion_label="WAIT", conditions_met=1, conditions_total=4,
            rsi=Decimal(50), price_vs_30d_avg_pct=Decimal(2), sharp_move=False,
        ),
    )
    save_screener_run(db, [row_1], run_at_1)
    assert db.query(ScreenerResult).count() == 1

    run_at_2 = datetime(2026, 8, 2, tzinfo=timezone.utc)
    row_2 = ScreenerRow(
        ticker="BBB",
        company_name="BBB Inc.",
        evaluation=ScreenerEvaluation(
            status="ok", current_price=Decimal(20), change_1d_pct=Decimal(-1),
            suggestion_label="BUY", conditions_met=3, conditions_total=4,
            rsi=Decimal(30), price_vs_30d_avg_pct=Decimal(-5), sharp_move=True,
        ),
    )
    save_screener_run(db, [row_2], run_at_2)

    rows = db.query(ScreenerResult).all()
    assert len(rows) == 1
    assert rows[0].ticker == "BBB"
    assert rows[0].run_at == run_at_2


def test_run_screener_batch_splits_success_and_failure(monkeypatch) -> None:
    monkeypatch.setattr(screener_service, "read_screener_universe", lambda: ["AAA", "BBB"])
    provider = FakeProvider(
        history_by_ticker={"AAA": _bars(30)},
        failing_history_tickers={"BBB"},
    )

    result = run_screener_batch(provider)

    assert [row.ticker for row in result.rows] == ["AAA"]
    assert [f.ticker for f in result.failures] == ["BBB"]
    assert result.run_at is not None


def test_get_latest_screener_run_never_run_is_empty(db) -> None:
    run = get_latest_screener_run(db)
    assert run.run_at is None
    assert run.rows == []


def test_get_latest_screener_run_returns_rows_and_run_at(db) -> None:
    run_at = datetime(2026, 8, 1, tzinfo=timezone.utc)
    row = ScreenerRow(
        ticker="AAA",
        company_name="AAA Inc.",
        evaluation=ScreenerEvaluation(
            status="ok", current_price=Decimal(10), change_1d_pct=Decimal(1),
            suggestion_label="WAIT", conditions_met=1, conditions_total=4,
            rsi=Decimal(50), price_vs_30d_avg_pct=Decimal(2), sharp_move=False,
        ),
    )
    save_screener_run(db, [row], run_at)

    run = get_latest_screener_run(db)
    assert run.run_at == run_at
    assert len(run.rows) == 1
    assert run.rows[0].ticker == "AAA"
