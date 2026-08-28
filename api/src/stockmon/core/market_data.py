from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class DailyBar:
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class Quote:
    price: Decimal
    as_of: datetime


class MarketDataError(Exception):
    """Raised by a MarketDataProvider when a fetch fails for one ticker."""


def merge_live_quote(bars: list[DailyBar], quote: Quote) -> list[DailyBar]:
    """Replaces the most recent bar's close with a live quote when that bar
    is the same trading day as the quote -- lets callers show a live
    intraday price instead of the last completed daily close. No-op when
    there's no bar for the quote's day (market not yet in session)."""
    if not bars or bars[-1].date != quote.as_of.date():
        return bars
    return [*bars[:-1], replace(bars[-1], close=quote.price)]


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        """Return daily bars for the last `days` calendar days, oldest first."""

    @abstractmethod
    def fetch_current_quote(self, ticker: str) -> Quote:
        """Return the latest available price for `ticker`."""

    @abstractmethod
    def fetch_company_name(self, ticker: str) -> str:
        """Resolve a ticker to its company name. Raises MarketDataError if
        the ticker can't be resolved -- this IS the "does this ticker
        exist" check for POST /api/stocks."""

    @abstractmethod
    def fetch_exchange(self, ticker: str) -> str | None:
        """Resolve a ticker to its primary exchange as a Google-Finance-style
        suffix (e.g. "NASDAQ", "NYSE"), for building news links. Non-critical:
        returns None rather than raising when the exchange can't be resolved
        or isn't a recognized one -- callers fall back to an exchange-less
        link rather than failing the whole request."""
