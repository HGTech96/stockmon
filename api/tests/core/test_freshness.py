from datetime import datetime, timezone

from stockmon.core.freshness import (
    NO_DATA_MESSAGE,
    REFRESH_NEVER_SUCCEEDED_MESSAGE,
    build_freshness,
    format_weekday_time,
)

NOW = datetime(2026, 8, 19, 18, 45, tzinfo=timezone.utc)


def test_never_refreshed_is_stale_with_now_as_data_as_of() -> None:
    freshness = build_freshness(
        now=NOW, last_attempted_at=None, last_succeeded_at=None, had_failures=False
    )
    assert freshness.data_as_of == NOW
    assert freshness.is_stale is True
    assert freshness.stale_message == NO_DATA_MESSAGE


def test_successful_refresh_is_fresh() -> None:
    succeeded = datetime(2026, 8, 19, 16, 0, tzinfo=timezone.utc)
    freshness = build_freshness(
        now=NOW, last_attempted_at=succeeded, last_succeeded_at=succeeded, had_failures=False
    )
    assert freshness.data_as_of == succeeded
    assert freshness.is_stale is False
    assert freshness.stale_message is None


def test_failed_refresh_with_prior_success_is_stale() -> None:
    succeeded = datetime(2026, 8, 17, 16, 0, tzinfo=timezone.utc)
    attempted = datetime(2026, 8, 19, 16, 0, tzinfo=timezone.utc)
    freshness = build_freshness(
        now=NOW, last_attempted_at=attempted, last_succeeded_at=succeeded, had_failures=True
    )
    assert freshness.data_as_of == succeeded
    assert freshness.is_stale is True
    assert freshness.stale_message == "Couldn't refresh — showing the last known prices from Monday, 4:00 PM."


def test_failed_refresh_with_no_prior_success_is_stale() -> None:
    attempted = datetime(2026, 8, 19, 16, 0, tzinfo=timezone.utc)
    freshness = build_freshness(
        now=NOW, last_attempted_at=attempted, last_succeeded_at=None, had_failures=True
    )
    assert freshness.data_as_of == NOW
    assert freshness.is_stale is True
    assert freshness.stale_message == REFRESH_NEVER_SUCCEEDED_MESSAGE


def test_format_weekday_time_morning() -> None:
    assert format_weekday_time(datetime(2026, 8, 17, 9, 5)) == "Monday, 9:05 AM"


def test_format_weekday_time_noon() -> None:
    assert format_weekday_time(datetime(2026, 8, 17, 12, 0)) == "Monday, 12:00 PM"


def test_format_weekday_time_midnight() -> None:
    assert format_weekday_time(datetime(2026, 8, 17, 0, 0)) == "Monday, 12:00 AM"
