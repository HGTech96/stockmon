from datetime import datetime

from sqlalchemy.orm import Session

from stockmon.core.freshness import NO_DATA_MESSAGE, Freshness, build_freshness
from stockmon.core.market_hours import get_market_status
from stockmon.db.refresh_status import get_or_create, record
from stockmon.services.refresh_service import RefreshResult


def get_freshness(db: Session, user_id: int, now: datetime | None = None) -> Freshness:
    status = get_or_create(db, user_id)
    return build_freshness(
        now=now or datetime.now().astimezone(),
        last_attempted_at=status.last_attempted_at,
        last_succeeded_at=status.last_succeeded_at,
        had_failures=status.had_failures,
    )


def get_live_freshness(now: datetime | None = None) -> Freshness:
    """For live, uncached reads with no stored refresh state (the
    screener's live-fetch detail endpoint) -- data_as_of is always now,
    never stale, since the data was just fetched."""
    now = now or datetime.now().astimezone()
    return Freshness(data_as_of=now, is_stale=False, stale_message=None, market_status=get_market_status(now))


def get_screener_freshness(run_at: datetime | None, now: datetime | None = None) -> Freshness:
    """The screener is a separate, unauthenticated/global subsystem (see
    CLAUDE.md) with its own freshness signal (the last batch run), never
    the per-user refresh_status table."""
    now = now or datetime.now().astimezone()
    market_status = get_market_status(now)
    if run_at is None:
        return Freshness(data_as_of=now, is_stale=True, stale_message=NO_DATA_MESSAGE, market_status=market_status)
    return Freshness(data_as_of=run_at, is_stale=False, stale_message=None, market_status=market_status)


def record_refresh_result(db: Session, user_id: int, result: RefreshResult) -> None:
    had_failures = bool(result.failed)
    record(
        db,
        user_id,
        attempted_at=result.data_as_of,
        succeeded=not had_failures,
        had_failures=had_failures,
    )
    db.commit()
