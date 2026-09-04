import warnings
from datetime import date, datetime, timedelta
from decimal import Decimal

import yfinance as yf
from curl_cffi import requests as curl_requests
from pandas.errors import Pandas4Warning

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote

# yfinance calls a pandas API deprecated in the pandas version this project
# pins (harmless, yfinance's issue to fix, not ours) on every history fetch.
# yfinance's own __init__ re-enables DeprecationWarning for its module, so
# this filter must be added after `import yfinance` to take precedence.
warnings.filterwarnings("ignore", category=Pandas4Warning)

# yf.Ticker(ticker) with no explicit `session=` opens a brand-new curl_cffi
# session (its own connection) on EVERY call and never closes it -- with
# YFinanceProvider instantiated fresh per-request (see api/dependencies.py)
# and 4 yf.Ticker() calls per provider method, those pile up as CLOSE_WAIT
# sockets to Yahoo's servers until the process hits its file-descriptor
# limit ("Too many open files" on refresh/screener runs after enough
# traffic). One shared, process-lifetime session -- matching yfinance's own
# default "impersonate=chrome" browser-TLS fingerprint, curl_cffi Sessions
# are safe to share across threads (thread-local curl handle per thread) --
# fixes it.
_SESSION = curl_requests.Session(impersonate="chrome")

# yfinance's fast_info["exchange"] short codes -> Google Finance's URL
# suffix. Deliberately small and conservative: an unrecognized code maps to
# None (link omits the suffix) rather than guessing wrong.
_EXCHANGE_SUFFIXES = {
    "NMS": "NASDAQ",  # Nasdaq Global Select
    "NGM": "NASDAQ",  # Nasdaq Global Market
    "NCM": "NASDAQ",  # Nasdaq Capital Market
    "NYQ": "NYSE",
    "ASE": "NYSEAMERICAN",
    "PCX": "NYSEARCA",
}


class YFinanceProvider(MarketDataProvider):
    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        start = date.today() - timedelta(days=days)
        end = date.today() + timedelta(days=1)
        try:
            history = yf.Ticker(ticker, session=_SESSION).history(start=start, end=end)
        except Exception as exc:
            raise MarketDataError(str(exc)) from exc

        if history.empty:
            raise MarketDataError(f"no price history returned for {ticker}")

        return [
            DailyBar(
                date=timestamp.date(),
                open=Decimal(str(row["Open"])),
                high=Decimal(str(row["High"])),
                low=Decimal(str(row["Low"])),
                close=Decimal(str(row["Close"])),
                volume=int(row["Volume"]),
            )
            for timestamp, row in history.iterrows()
        ]

    def fetch_current_quote(self, ticker: str) -> Quote:
        try:
            last_price = yf.Ticker(ticker, session=_SESSION).fast_info["last_price"]
        except Exception as exc:
            raise MarketDataError(str(exc)) from exc

        if last_price is None:
            raise MarketDataError(f"no current price available for {ticker}")

        return Quote(price=Decimal(str(last_price)), as_of=datetime.now().astimezone())

    def fetch_company_name(self, ticker: str) -> str:
        try:
            info = yf.Ticker(ticker, session=_SESSION).info
        except Exception as exc:
            raise MarketDataError(str(exc)) from exc

        name = (info.get("longName") or info.get("shortName") or "").strip()
        if not name:
            raise MarketDataError(f"no company name available for {ticker}")
        return name

    def fetch_exchange(self, ticker: str) -> str | None:
        try:
            code = yf.Ticker(ticker, session=_SESSION).fast_info.get("exchange")
        except Exception:
            return None
        return _EXCHANGE_SUFFIXES.get(code)
