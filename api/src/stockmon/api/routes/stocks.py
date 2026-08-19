from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.dashboard import DashboardResponse
from stockmon.api.schemas.stock_detail import StockDetailResponse
from stockmon.db.session import get_db
from stockmon.services.dashboard_service import build_dashboard
from stockmon.services.freshness_service import get_freshness
from stockmon.services.stock_detail_service import get_stock_detail

router = APIRouter()


@router.get("/api/stocks", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    meta = MetaSchema.from_core(get_freshness(db))
    dashboard = build_dashboard(db)
    return DashboardResponse.from_core(meta, dashboard)


@router.get("/api/stocks/{ticker}", response_model=StockDetailResponse)
def get_stock(ticker: str, db: Session = Depends(get_db)) -> StockDetailResponse:
    meta = MetaSchema.from_core(get_freshness(db))
    detail = get_stock_detail(db, ticker)
    return StockDetailResponse.from_core(meta, detail)
