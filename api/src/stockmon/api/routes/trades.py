from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.schemas.trade import TradeRequest, TradeResponse
from stockmon.db.session import get_db
from stockmon.services.trade_service import record_trade

router = APIRouter()


@router.post("/api/trades", response_model=TradeResponse, status_code=201)
def create_trade(body: TradeRequest, db: Session = Depends(get_db)) -> TradeResponse:
    result = record_trade(db, body.ticker, body.action, body.shares, body.price_per_share, body.date)
    return TradeResponse.from_core(body.ticker, result)
