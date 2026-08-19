from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from stockmon.core.market_data import MarketDataError, MarketDataProvider
from stockmon.db.daily_prices import upsert_daily_prices
from stockmon.db.models import Stock

DEFAULT_HISTORY_DAYS = 60


@dataclass(frozen=True)
class RefreshFailure:
    ticker: str
    error: str


@dataclass(frozen=True)
class RefreshResult:
    refreshed: list[str]
    failed: list[RefreshFailure]
    data_as_of: datetime


def refresh_all_stocks(
    db: Session, provider: MarketDataProvider, days: int = DEFAULT_HISTORY_DAYS
) -> RefreshResult:
    refreshed: list[str] = []
    failed: list[RefreshFailure] = []

    for stock in db.query(Stock).all():
        try:
            bars = provider.fetch_daily_history(stock.ticker, days)
            upsert_daily_prices(db, stock.id, bars)
            db.commit()
            refreshed.append(stock.ticker)
        except MarketDataError as exc:
            db.rollback()
            failed.append(RefreshFailure(ticker=stock.ticker, error=str(exc)))

    return RefreshResult(
        refreshed=refreshed,
        failed=failed,
        data_as_of=datetime.now().astimezone(),
    )
