from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.deps import get_current_user
from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.portfolio import PortfolioResponse
from stockmon.db.models import User
from stockmon.db.session import get_db
from stockmon.services.freshness_service import get_freshness
from stockmon.services.portfolio_service import get_portfolio

router = APIRouter()


@router.get("/api/portfolio", response_model=PortfolioResponse)
def read_portfolio(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> PortfolioResponse:
    meta = MetaSchema.from_core(get_freshness(db, current_user.id))
    portfolio = get_portfolio(db, current_user.id)
    return PortfolioResponse.from_core(meta, portfolio)
