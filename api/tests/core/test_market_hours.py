from datetime import datetime
from zoneinfo import ZoneInfo

from stockmon.core.market_hours import NY_TZ, get_market_status

UTC = ZoneInfo("UTC")


def _ny(year, month, day, hour, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=NY_TZ)


def test_weekday_during_hours_is_open() -> None:
    # Thursday, Aug 27 2026, noon ET
    result = get_market_status(_ny(2026, 8, 27, 12, 0))
    assert result.state == "open"
    assert result.label == "Market Open"


def test_weekday_before_open_is_pre_market() -> None:
    result = get_market_status(_ny(2026, 8, 27, 8, 0))
    assert result.state == "pre_market"
    assert result.label == "Pre-Market Open"


def test_weekday_after_close_is_after_hours() -> None:
    result = get_market_status(_ny(2026, 8, 27, 17, 0))
    assert result.state == "after_hours"
    assert result.label == "After Hours"


def test_weekend_is_closed_weekend() -> None:
    # Saturday, Aug 29 2026, noon ET
    result = get_market_status(_ny(2026, 8, 29, 12, 0))
    assert result.state == "closed_weekend"
    assert result.label == "Market Closed"


def test_holiday_is_closed_holiday() -> None:
    # Christmas Day 2026 (Friday) -- not a weekend, must hit the holiday branch
    result = get_market_status(_ny(2026, 12, 25, 12, 0))
    assert result.state == "closed_holiday"
    assert result.label == "Market Closed"


def test_exact_open_boundary_is_open() -> None:
    result = get_market_status(_ny(2026, 8, 27, 9, 30))
    assert result.state == "open"


def test_exact_close_boundary_is_after_hours() -> None:
    result = get_market_status(_ny(2026, 8, 27, 16, 0))
    assert result.state == "after_hours"


def test_converts_non_eastern_timezone_input() -> None:
    # 13:00 UTC on Aug 27 2026 == 09:00 ET (EDT, UTC-4 in August) -> pre-market
    utc_time = datetime(2026, 8, 27, 13, 0, tzinfo=UTC)
    result = get_market_status(utc_time)
    assert result.state == "pre_market"
