from abc import ABC, abstractmethod
from dataclasses import dataclass
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
