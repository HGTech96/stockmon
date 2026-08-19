from datetime import date, datetime, timedelta
from decimal import Decimal

import yfinance as yf

from stockmon.core.market_data import DailyBar, MarketDataError, MarketDataProvider, Quote


class YFinanceProvider(MarketDataProvider):
    def fetch_daily_history(self, ticker: str, days: int) -> list[DailyBar]:
        start = date.today() - timedelta(days=days)
        end = date.today() + timedelta(days=1)
        try:
            history = yf.Ticker(ticker).history(start=start, end=end)
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
            last_price = yf.Ticker(ticker).fast_info["last_price"]
        except Exception as exc:
            raise MarketDataError(str(exc)) from exc

        if last_price is None:
            raise MarketDataError(f"no current price available for {ticker}")

        return Quote(price=Decimal(str(last_price)), as_of=datetime.now().astimezone())
