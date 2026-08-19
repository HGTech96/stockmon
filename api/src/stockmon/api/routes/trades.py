from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.trade import TradeHistoryResponse, TradeRequest, TradeResponse
from stockmon.db.session import get_db
from stockmon.services.freshness_service import get_freshness
from stockmon.services.trade_service import list_trade_history, record_trade

router = APIRouter()


@router.post("/api/trades", response_model=TradeResponse, status_code=201)
def create_trade(body: TradeRequest, db: Session = Depends(get_db)) -> TradeResponse:
    result = record_trade(db, body.ticker, body.action, body.shares, body.price_per_share, body.date)
    return TradeResponse.from_core(body.ticker, result)


@router.get("/api/trades", response_model=TradeHistoryResponse)
def read_trades(db: Session = Depends(get_db)) -> TradeHistoryResponse:
    meta = MetaSchema.from_core(get_freshness(db))
    entries = list_trade_history(db)
    return TradeHistoryResponse.from_core(meta, entries)
