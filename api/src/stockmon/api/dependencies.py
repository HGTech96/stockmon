from stockmon.core.market_data import MarketDataProvider
from stockmon.services.yfinance_provider import YFinanceProvider


def get_market_data_provider() -> MarketDataProvider:
    return YFinanceProvider()
