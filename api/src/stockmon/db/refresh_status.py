from datetime import datetime

from sqlalchemy.orm import Session

from stockmon.db.models import RefreshStatus


def get_or_create(db: Session, user_id: int) -> RefreshStatus:
    status = db.get(RefreshStatus, user_id)
    if status is None:
        status = RefreshStatus(user_id=user_id)
        db.add(status)
        db.flush()
    return status


def record(db: Session, user_id: int, *, attempted_at: datetime, succeeded: bool, had_failures: bool) -> RefreshStatus:
    status = get_or_create(db, user_id)
    status.last_attempted_at = attempted_at
    status.had_failures = had_failures
    if succeeded:
        status.last_succeeded_at = attempted_at
    return status
