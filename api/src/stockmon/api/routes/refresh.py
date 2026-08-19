from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.schemas.refresh import RefreshFailureItem, RefreshResponse
from stockmon.core.market_data import MarketDataProvider
from stockmon.db.session import get_db
from stockmon.services.freshness_service import record_refresh_result
from stockmon.services.refresh_service import refresh_all_stocks
from stockmon.services.yfinance_provider import YFinanceProvider

router = APIRouter()


def get_market_data_provider() -> MarketDataProvider:
    return YFinanceProvider()


@router.post("/api/refresh", response_model=RefreshResponse)
def refresh(
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> RefreshResponse:
    result = refresh_all_stocks(db, provider)
    record_refresh_result(db, result)
    return RefreshResponse(
        refreshed=result.refreshed,
        failed=[RefreshFailureItem(ticker=f.ticker, error=f.error) for f in result.failed],
        data_as_of=result.data_as_of,
    )
