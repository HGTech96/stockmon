from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session

from stockmon.api.deps import SESSION_COOKIE_NAME, get_current_user
from stockmon.api.schemas.auth import LoginRequest, UserSchema
from stockmon.config import settings as app_settings
from stockmon.db.models import User as UserRow
from stockmon.db.session import get_db
from stockmon.services.auth_service import SESSION_LIFETIME, authenticate, create_session, delete_session

router = APIRouter()


@router.post("/api/auth/login", response_model=UserSchema)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserSchema:
    user = authenticate(db, body.username, body.password)
    session = create_session(db, user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.id,
        httponly=True,
        secure=app_settings.environment == "production",
        samesite="lax",
        max_age=int(SESSION_LIFETIME.total_seconds()),
    )
    return UserSchema.from_row(user)


@router.post("/api/auth/logout", status_code=204)
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> None:
    if session_id is not None:
        delete_session(db, session_id)
    response.delete_cookie(SESSION_COOKIE_NAME)


@router.get("/api/auth/me", response_model=UserSchema)
def me(current_user: UserRow = Depends(get_current_user)) -> UserSchema:
    return UserSchema.from_row(current_user)
