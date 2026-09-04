from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.dependencies import get_market_data_provider
from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.screener import ScreenerRefreshResponse, ScreenerResponse
from stockmon.api.schemas.stock_detail import StockDetailResponse
from stockmon.core.market_data import MarketDataProvider
from stockmon.db.session import get_db
from stockmon.services.freshness_service import get_live_freshness, get_screener_freshness
from stockmon.services.screener_detail_service import get_screener_stock_detail
from stockmon.services.screener_service import get_latest_screener_run, run_screener_batch, save_screener_run

router = APIRouter()


@router.get("/api/screener", response_model=ScreenerResponse)
def get_screener(db: Session = Depends(get_db)) -> ScreenerResponse:
    run = get_latest_screener_run(db)
    meta = MetaSchema.from_core(get_screener_freshness(run.run_at))
    return ScreenerResponse.from_core(meta, run)


@router.post("/api/screener/refresh", response_model=ScreenerRefreshResponse)
def refresh_screener(
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> ScreenerRefreshResponse:
    result = run_screener_batch(provider)
    save_screener_run(db, result.rows, result.run_at)
    return ScreenerRefreshResponse.from_core(result)


@router.get("/api/screener/{ticker}/detail", response_model=StockDetailResponse)
def get_screener_detail(
    ticker: str,
    provider: MarketDataProvider = Depends(get_market_data_provider),
) -> StockDetailResponse:
    meta = MetaSchema.from_core(get_live_freshness())
    detail = get_screener_stock_detail(provider, ticker)
    return StockDetailResponse.from_core(meta, detail)
