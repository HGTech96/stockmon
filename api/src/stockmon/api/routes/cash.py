from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.deps import get_current_user
from stockmon.api.schemas.cash import CashEventRequest, CashEventResponse, CashListResponse
from stockmon.api.schemas.common import MetaSchema
from stockmon.db.models import User
from stockmon.db.session import get_db
from stockmon.services.cash_service import delete_cash_event, list_cash_events, record_cash_event
from stockmon.services.freshness_service import get_freshness

router = APIRouter()


@router.get("/api/cash", response_model=CashListResponse)
def read_cash(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> CashListResponse:
    meta = MetaSchema.from_core(get_freshness(db, current_user.id))
    entries, cash_available = list_cash_events(db, current_user.id)
    return CashListResponse.from_core(meta, entries, cash_available)


@router.post("/api/cash", response_model=CashEventResponse, status_code=201)
def create_cash_event(
    body: CashEventRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> CashEventResponse:
    row, cash_available = record_cash_event(db, current_user.id, body.type, body.amount_usd, body.date)
    return CashEventResponse.from_core(row, cash_available)


@router.delete("/api/cash/{id}", status_code=204)
def remove_cash_event(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    delete_cash_event(db, current_user.id, id)
