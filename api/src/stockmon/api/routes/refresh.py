from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.dependencies import get_market_data_provider
from stockmon.api.deps import get_current_user
from stockmon.api.schemas.refresh import RefreshFailureItem, RefreshResponse
from stockmon.core.market_data import MarketDataProvider
from stockmon.db.models import User
from stockmon.db.session import get_db
from stockmon.services.freshness_service import record_refresh_result
from stockmon.services.refresh_service import refresh_all_stocks

router = APIRouter()


@router.post("/api/refresh", response_model=RefreshResponse)
def refresh(
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
    current_user: User = Depends(get_current_user),
) -> RefreshResponse:
    result = refresh_all_stocks(db, provider, current_user.id)
    record_refresh_result(db, current_user.id, result)
    return RefreshResponse(
        refreshed=result.refreshed,
        failed=[RefreshFailureItem(ticker=f.ticker, error=f.error) for f in result.failed],
        data_as_of=result.data_as_of,
    )
