from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, merge_live_quote
from stockmon.db.daily_prices import upsert_daily_prices
from stockmon.db.models import Ticker, WatchlistEntry

DEFAULT_HISTORY_DAYS = 60


def overlay_live_price(provider: MarketDataProvider, ticker: str, bars: list[DailyBar]) -> list[DailyBar]:
    """Fetches a live quote and overlays it onto today's bar via
    merge_live_quote, so currentPrice reflects the live price rather than
    the last completed close. A quote-fetch hiccup falls back to the
    unmodified bars -- valid daily history should never be discarded over it."""
    if not bars or bars[-1].date != date.today():
        return bars
    try:
        quote = provider.fetch_current_quote(ticker)
    except MarketDataError:
        return bars
    return merge_live_quote(bars, quote)


@dataclass(frozen=True)
class RefreshFailure:
    ticker: str
    error: str


@dataclass(frozen=True)
class RefreshResult:
    refreshed: list[str]
    failed: list[RefreshFailure]
    data_as_of: datetime


def refresh_stock(
    db: Session, provider: MarketDataProvider, ticker_row: Ticker, days: int = DEFAULT_HISTORY_DAYS
) -> RefreshFailure | None:
    """One ticker's fetch+upsert+commit, success=None / failure=RefreshFailure.
    Used by refresh_all_stocks (looped) and add_stock_to_watchlist (single
    call) so both paths share one implementation. Operates on the shared
    Ticker row -- refreshing benefits every user tracking it."""
    try:
        bars = provider.fetch_daily_history(ticker_row.ticker, days)
        bars = overlay_live_price(provider, ticker_row.ticker, bars)
        upsert_daily_prices(db, ticker_row.id, bars)
        db.commit()
        return None
    except MarketDataError as exc:
        db.rollback()
        return RefreshFailure(ticker=ticker_row.ticker, error=str(exc))


def refresh_all_stocks(
    db: Session, provider: MarketDataProvider, user_id: int, days: int = DEFAULT_HISTORY_DAYS
) -> RefreshResult:
    """Refreshes every ticker on this user's watchlist. Since Ticker rows
    are shared, this also freshens the data for any other user tracking
    the same ticker."""
    refreshed: list[str] = []
    failed: list[RefreshFailure] = []

    tickers = (
        db.query(Ticker)
        .join(WatchlistEntry, WatchlistEntry.ticker_id == Ticker.id)
        .filter(WatchlistEntry.user_id == user_id)
        .all()
    )
    for ticker_row in tickers:
        failure = refresh_stock(db, provider, ticker_row, days)
        if failure is None:
            refreshed.append(ticker_row.ticker)
        else:
            failed.append(failure)

    return RefreshResult(
        refreshed=refreshed,
        failed=failed,
        data_as_of=datetime.now().astimezone(),
    )
