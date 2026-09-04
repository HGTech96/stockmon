from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from stockmon.db.models import User as UserRow
from stockmon.db.session import get_db
from stockmon.services.auth_service import get_user_by_session

SESSION_COOKIE_NAME = "session_id"


class NotAuthenticatedError(Exception):
    def __init__(self) -> None:
        super().__init__("Not authenticated")


def get_current_user(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> UserRow:
    if session_id is None:
        raise NotAuthenticatedError()
    user = get_user_by_session(db, session_id)
    if user is None:
        raise NotAuthenticatedError()
    return user
