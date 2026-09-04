from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.deps import get_current_user
from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.trade import TradeHistoryResponse, TradeRequest, TradeResponse, TradeUpdateRequest
from stockmon.db.models import User
from stockmon.db.session import get_db
from stockmon.services.freshness_service import get_freshness
from stockmon.services.trade_service import delete_trade, list_trade_history, record_trade, update_trade

router = APIRouter()


@router.post("/api/trades", response_model=TradeResponse, status_code=201)
def create_trade(
    body: TradeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> TradeResponse:
    result = record_trade(db, current_user.id, body.ticker, body.action, body.shares, body.price_per_share, body.date)
    return TradeResponse.from_core(body.ticker, result)


@router.get("/api/trades", response_model=TradeHistoryResponse)
def read_trades(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TradeHistoryResponse:
    meta = MetaSchema.from_core(get_freshness(db, current_user.id))
    entries = list_trade_history(db, current_user.id)
    return TradeHistoryResponse.from_core(meta, entries)


@router.put("/api/trades/{id}", response_model=TradeResponse)
def edit_trade(
    id: int, body: TradeUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> TradeResponse:
    result = update_trade(db, current_user.id, id, body.shares, body.price_per_share, body.date)
    return TradeResponse.from_core(result.trade.watchlist_entry.ticker.ticker, result)


@router.delete("/api/trades/{id}", status_code=204)
def remove_trade(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    delete_trade(db, current_user.id, id)
