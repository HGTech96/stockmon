from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

NY_TZ = ZoneInfo("America/New_York")
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

MarketState = Literal["open", "pre_market", "after_hours", "closed_weekend", "closed_holiday"]

# NYSE full-closure holidays. Source: NYSE Group's official 2025/2026/2027
# holiday calendar (theice.com press release, Nov 2024). Needs a manual
# top-up once 2028 approaches -- there's no library dependency for this,
# it's a short fixed list refreshed ~once a year.
US_MARKET_HOLIDAYS: set[date] = {
    # 2025
    date(2025, 1, 1), date(2025, 1, 20), date(2025, 2, 17), date(2025, 4, 18),
    date(2025, 5, 26), date(2025, 6, 19), date(2025, 7, 4), date(2025, 9, 1),
    date(2025, 11, 27), date(2025, 12, 25),
    # 2026
    date(2026, 1, 1), date(2026, 1, 19), date(2026, 2, 16), date(2026, 4, 3),
    date(2026, 5, 25), date(2026, 6, 19), date(2026, 7, 3), date(2026, 9, 7),
    date(2026, 11, 26), date(2026, 12, 25),
    # 2027
    date(2027, 1, 1), date(2027, 1, 18), date(2027, 2, 15), date(2027, 3, 26),
    date(2027, 5, 31), date(2027, 6, 18), date(2027, 7, 5), date(2027, 9, 6),
    date(2027, 11, 25), date(2027, 12, 24),
}

_LABELS: dict[MarketState, str] = {
    "open": "Market Open",
    "pre_market": "Pre-Market Open",
    "after_hours": "After Hours",
    "closed_weekend": "Market Closed",
    "closed_holiday": "Market Closed",
}


@dataclass(frozen=True)
class MarketStatus:
    state: MarketState
    label: str


def get_market_status(now: datetime) -> MarketStatus:
    """NYSE regular-hours check only (9:30am-4pm ET, Mon-Fri, minus
    holidays) -- no pre/post-market session distinction beyond that, no
    early-close-day handling (rare, cosmetic only)."""
    ny_now = now.astimezone(NY_TZ)
    if ny_now.weekday() >= 5:
        state: MarketState = "closed_weekend"
    elif ny_now.date() in US_MARKET_HOLIDAYS:
        state = "closed_holiday"
    elif ny_now.time() < MARKET_OPEN:
        state = "pre_market"
    elif ny_now.time() >= MARKET_CLOSE:
        state = "after_hours"
    else:
        state = "open"
    return MarketStatus(state=state, label=_LABELS[state])
