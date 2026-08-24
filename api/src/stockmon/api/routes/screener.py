from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.schemas.common import MetaSchema
from stockmon.api.schemas.screener import ScreenerResponse
from stockmon.db.session import get_db
from stockmon.services.freshness_service import get_freshness
from stockmon.services.screener_service import get_latest_screener_run

router = APIRouter()


@router.get("/api/screener", response_model=ScreenerResponse)
def get_screener(db: Session = Depends(get_db)) -> ScreenerResponse:
    meta = MetaSchema.from_core(get_freshness(db))
    run = get_latest_screener_run(db)
    return ScreenerResponse.from_core(meta, run)
