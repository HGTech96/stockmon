from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from stockmon.api.deps import get_current_user
from stockmon.api.schemas.settings import (
    SettingsResponse,
    UpdateDefaultTargetRequest,
    UpdatePositionTargetRequest,
)
from stockmon.db.models import User
from stockmon.db.session import get_db
from stockmon.services.settings_service import (
    get_settings,
    remove_position_target,
    set_position_target,
    update_default_target,
)

router = APIRouter()


@router.get("/api/settings", response_model=SettingsResponse)
def read_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> SettingsResponse:
    return SettingsResponse.from_core(get_settings(db, current_user.id))


@router.put("/api/settings", response_model=SettingsResponse)
def update_settings(
    body: UpdateDefaultTargetRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> SettingsResponse:
    return SettingsResponse.from_core(
        update_default_target(db, current_user.id, body.default_profit_target_dollars)
    )


@router.put("/api/settings/targets/{ticker}", response_model=SettingsResponse)
def update_position_target(
    ticker: str,
    body: UpdatePositionTargetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SettingsResponse:
    return SettingsResponse.from_core(set_position_target(db, current_user.id, ticker, body.target_dollars))


@router.delete("/api/settings/targets/{ticker}", status_code=204)
def remove_position_target_route(
    ticker: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    remove_position_target(db, current_user.id, ticker)
