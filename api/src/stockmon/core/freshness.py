from dataclasses import dataclass
from datetime import datetime

from stockmon.core.market_hours import MarketStatus, get_market_status

NO_DATA_MESSAGE = "No data yet — run a refresh to load prices."
REFRESH_FAILED_MESSAGE = "Couldn't refresh — showing the last known prices from {when}."
REFRESH_NEVER_SUCCEEDED_MESSAGE = "Couldn't refresh — no successful refresh yet."


@dataclass(frozen=True)
class Freshness:
    data_as_of: datetime
    is_stale: bool
    stale_message: str | None
    market_status: MarketStatus


def format_weekday_time(dt: datetime) -> str:
    """e.g. 'Monday, 4:00 PM'."""
    hour = dt.hour % 12 or 12
    period = "AM" if dt.hour < 12 else "PM"
    return f"{dt.strftime('%A')}, {hour}:{dt.minute:02d} {period}"


def build_freshness(
    now: datetime,
    last_attempted_at: datetime | None,
    last_succeeded_at: datetime | None,
    had_failures: bool,
) -> Freshness:
    """Never refreshed (no attempt recorded) -> stale, data_as_of=now.
    Last refresh attempt had failures -> stale, data_as_of is the last
    successful refresh (or now if none ever succeeded).
    Otherwise -> fresh, data_as_of is the last successful refresh."""
    market_status = get_market_status(now)

    if last_attempted_at is None:
        return Freshness(
            data_as_of=now, is_stale=True, stale_message=NO_DATA_MESSAGE, market_status=market_status
        )

    if had_failures:
        if last_succeeded_at is None:
            return Freshness(
                data_as_of=now,
                is_stale=True,
                stale_message=REFRESH_NEVER_SUCCEEDED_MESSAGE,
                market_status=market_status,
            )
        message = REFRESH_FAILED_MESSAGE.format(when=format_weekday_time(last_succeeded_at))
        return Freshness(
            data_as_of=last_succeeded_at, is_stale=True, stale_message=message, market_status=market_status
        )

    assert last_succeeded_at is not None
    return Freshness(
        data_as_of=last_succeeded_at, is_stale=False, stale_message=None, market_status=market_status
    )
