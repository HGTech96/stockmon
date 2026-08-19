from datetime import datetime

from sqlalchemy.orm import Session

from stockmon.core.freshness import Freshness, build_freshness
from stockmon.db.refresh_status import get_or_create, record
from stockmon.services.refresh_service import RefreshResult


def get_freshness(db: Session, now: datetime | None = None) -> Freshness:
    status = get_or_create(db)
    return build_freshness(
        now=now or datetime.now().astimezone(),
        last_attempted_at=status.last_attempted_at,
        last_succeeded_at=status.last_succeeded_at,
        had_failures=status.had_failures,
    )


def record_refresh_result(db: Session, result: RefreshResult) -> None:
    had_failures = bool(result.failed)
    record(
        db,
        attempted_at=result.data_as_of,
        succeeded=not had_failures,
        had_failures=had_failures,
    )
    db.commit()
