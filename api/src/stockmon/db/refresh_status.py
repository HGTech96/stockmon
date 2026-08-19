from datetime import datetime

from sqlalchemy.orm import Session

from stockmon.db.models import RefreshStatus

SINGLETON_ID = 1


def get_or_create(db: Session) -> RefreshStatus:
    status = db.get(RefreshStatus, SINGLETON_ID)
    if status is None:
        status = RefreshStatus(id=SINGLETON_ID)
        db.add(status)
        db.flush()
    return status


def record(db: Session, *, attempted_at: datetime, succeeded: bool, had_failures: bool) -> RefreshStatus:
    status = get_or_create(db)
    status.last_attempted_at = attempted_at
    status.had_failures = had_failures
    if succeeded:
        status.last_succeeded_at = attempted_at
    return status
