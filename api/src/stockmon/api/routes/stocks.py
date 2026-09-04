from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.dependencies import get_market_data_provider
from stockmon.api.deps import get_current_user
from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.dashboard import DashboardResponse
from stockmon.api.schemas.stock import AddStockRequest, AddStockResponse
from stockmon.api.schemas.stock_detail import AnalysisSchema, SetAnalysisRequest, StockDetailResponse
from stockmon.core.market_data import MarketDataProvider
from stockmon.db.models import User
from stockmon.db.session import get_db
from stockmon.services.dashboard_service import build_dashboard
from stockmon.services.freshness_service import get_freshness
from stockmon.services.stock_detail_service import get_stock_detail
from stockmon.services.stock_service import add_stock_to_watchlist, clear_analysis, set_analysis

router = APIRouter()


@router.get("/api/stocks", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> DashboardResponse:
    meta = MetaSchema.from_core(get_freshness(db, current_user.id))
    dashboard = build_dashboard(db, current_user.id)
    return DashboardResponse.from_core(meta, dashboard)


@router.post("/api/stocks", response_model=AddStockResponse, status_code=201)
def add_stock(
    body: AddStockRequest,
    db: Session = Depends(get_db),
    provider: MarketDataProvider = Depends(get_market_data_provider),
    current_user: User = Depends(get_current_user),
) -> AddStockResponse:
    result = add_stock_to_watchlist(db, provider, current_user.id, body.ticker)
    return AddStockResponse.from_core(result)


@router.get("/api/stocks/{ticker}", response_model=StockDetailResponse)
def get_stock(
    ticker: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StockDetailResponse:
    meta = MetaSchema.from_core(get_freshness(db, current_user.id))
    detail = get_stock_detail(db, current_user.id, ticker)
    return StockDetailResponse.from_core(meta, detail)


@router.put("/api/stocks/{ticker}/analysis", response_model=AnalysisSchema)
def set_analysis_route(
    ticker: str,
    body: SetAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisSchema:
    return AnalysisSchema.from_core(set_analysis(db, current_user.id, ticker, body.date, body.value))


@router.delete("/api/stocks/{ticker}/analysis", status_code=204)
def clear_analysis_route(
    ticker: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    clear_analysis(db, current_user.id, ticker)
