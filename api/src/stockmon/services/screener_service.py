from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from stockmon.core.market_data import MarketDataError, MarketDataProvider
from stockmon.core.screener import ScreenerEvaluation, evaluate_screener_bars
from stockmon.db.models import ScreenerResult
from stockmon.services.refresh_service import DEFAULT_HISTORY_DAYS

# api/src/stockmon/services/screener_service.py -> parents[4] = repo root
SCREENER_STOCKS_PATH = Path(__file__).resolve().parents[4] / "screener_stocks.txt"


@dataclass(frozen=True)
class ScreenerFetchFailure:
    ticker: str
    error: str


@dataclass(frozen=True)
class ScreenerRow:
    ticker: str
    company_name: str
    evaluation: ScreenerEvaluation


@dataclass(frozen=True)
class ScreenerRun:
    run_at: datetime | None
    rows: list[ScreenerResult]


def read_screener_universe(path: Path = SCREENER_STOCKS_PATH) -> list[str]:
    """One ticker per line, blank lines ignored, uppercased and stripped."""
    with open(path) as fileobj:
        return [line.strip().upper() for line in fileobj if line.strip()]


def fetch_and_evaluate_ticker(provider: MarketDataProvider, ticker: str) -> ScreenerRow | ScreenerFetchFailure:
    """History fetch failure -> skip (ScreenerFetchFailure). Company-name
    fetch failure after a successful history fetch falls back to the ticker
    symbol as company_name -- the name is cosmetic, the analysis isn't --
    logging a quiet notice so a systematically-nameless run stays visible."""
    try:
        bars = provider.fetch_daily_history(ticker, DEFAULT_HISTORY_DAYS)
    except MarketDataError as exc:
        return ScreenerFetchFailure(ticker=ticker, error=str(exc))

    try:
        company_name = provider.fetch_company_name(ticker).strip() or ticker
    except MarketDataError:
        print(f"{ticker}: name unavailable, using symbol")
        company_name = ticker

    evaluation = evaluate_screener_bars(bars)
    return ScreenerRow(ticker=ticker, company_name=company_name, evaluation=evaluation)


def save_screener_run(db: Session, rows: list[ScreenerRow], run_at: datetime) -> None:
    """Truncate + rewrite in one transaction: the table always holds only
    the latest run's rows."""
    db.query(ScreenerResult).delete()
    db.add_all(
        ScreenerResult(
            ticker=row.ticker,
            company_name=row.company_name,
            current_price=row.evaluation.current_price,
            change_1d_pct=row.evaluation.change_1d_pct,
            status=row.evaluation.status,
            suggestion=row.evaluation.suggestion_label,
            conditions_met=row.evaluation.conditions_met,
            conditions_total=row.evaluation.conditions_total,
            rsi=row.evaluation.rsi,
            price_vs_30d_avg_pct=row.evaluation.price_vs_30d_avg_pct,
            sharp_move=row.evaluation.sharp_move,
            run_at=run_at,
        )
        for row in rows
    )
    db.commit()


def get_latest_screener_run(db: Session) -> ScreenerRun:
    rows = db.query(ScreenerResult).order_by(ScreenerResult.ticker).all()
    if not rows:
        return ScreenerRun(run_at=None, rows=[])
    return ScreenerRun(run_at=rows[0].run_at, rows=rows)
