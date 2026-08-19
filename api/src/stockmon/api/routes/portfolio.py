from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.portfolio import PortfolioResponse
from stockmon.db.session import get_db
from stockmon.services.freshness_service import get_freshness
from stockmon.services.portfolio_service import get_portfolio

router = APIRouter()


@router.get("/api/portfolio", response_model=PortfolioResponse)
def read_portfolio(db: Session = Depends(get_db)) -> PortfolioResponse:
    meta = MetaSchema.from_core(get_freshness(db))
    portfolio = get_portfolio(db)
    return PortfolioResponse.from_core(meta, portfolio)
