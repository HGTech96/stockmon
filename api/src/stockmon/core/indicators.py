from dataclasses import dataclass
from decimal import Decimal

from stockmon.core.market_data import DailyBar

MIN_HISTORY_DAYS = 30
RSI_PERIOD = 14

HUNDRED = Decimal(100)


class InsufficientHistoryError(Exception):
    def __init__(self, available: int, required: int = MIN_HISTORY_DAYS) -> None:
        self.available = available
        self.required = required
        super().__init__(f"need at least {required} days of history, got {available}")


@dataclass(frozen=True)
class Indicators:
    current_price: Decimal
    change_1d_pct: Decimal
    change_7d_pct: Decimal
    thirty_day_average: Decimal
    thirty_day_high: Decimal
    thirty_day_low: Decimal
    distance_from_high_pct: Decimal
    distance_from_low_pct: Decimal
    rsi: Decimal
    todays_volume: int
    average_volume: Decimal
    volume_vs_average_pct: Decimal


def calculate_indicators(bars: list[DailyBar]) -> Indicators:
    """bars must be sorted oldest-first. Raises InsufficientHistoryError if
    fewer than MIN_HISTORY_DAYS bars are supplied. 30-day metrics use the
    last MIN_HISTORY_DAYS bars; RSI uses the entire supplied list."""
    if len(bars) < MIN_HISTORY_DAYS:
        raise InsufficientHistoryError(available=len(bars))

    window = bars[-MIN_HISTORY_DAYS:]
    current_price = bars[-1].close

    change_1d_pct = _pct_change(bars[-2].close, current_price)
    change_7d_pct = _pct_change(bars[-8].close, current_price)

    closes = [bar.close for bar in window]
    thirty_day_average = sum(closes) / Decimal(len(closes))
    thirty_day_high = max(bar.high for bar in window)
    thirty_day_low = min(bar.low for bar in window)

    distance_from_high_pct = _pct_change(thirty_day_high, current_price)
    distance_from_low_pct = _pct_change(thirty_day_low, current_price)

    rsi = _wilder_rsi([bar.close for bar in bars])

    todays_volume = bars[-1].volume
    volumes = [bar.volume for bar in window]
    average_volume = Decimal(sum(volumes)) / Decimal(len(volumes))
    if average_volume == 0:
        volume_vs_average_pct = Decimal(0)
    else:
        volume_vs_average_pct = Decimal(todays_volume) / average_volume * HUNDRED

    return Indicators(
        current_price=current_price,
        change_1d_pct=change_1d_pct,
        change_7d_pct=change_7d_pct,
        thirty_day_average=thirty_day_average,
        thirty_day_high=thirty_day_high,
        thirty_day_low=thirty_day_low,
        distance_from_high_pct=distance_from_high_pct,
        distance_from_low_pct=distance_from_low_pct,
        rsi=rsi,
        todays_volume=todays_volume,
        average_volume=average_volume,
        volume_vs_average_pct=volume_vs_average_pct,
    )


def _pct_change(base: Decimal, current: Decimal) -> Decimal:
    if base == 0:
        return Decimal(0)
    return (current - base) / base * HUNDRED


def _wilder_rsi(closes: list[Decimal], period: int = RSI_PERIOD) -> Decimal:
    if len(closes) < period + 1:
        raise InsufficientHistoryError(available=len(closes), required=period + 1)

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(delta, Decimal(0)) for delta in deltas]
    losses = [max(-delta, Decimal(0)) for delta in deltas]

    avg_gain = sum(gains[:period]) / Decimal(period)
    avg_loss = sum(losses[:period]) / Decimal(period)

    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / Decimal(period)
        avg_loss = (avg_loss * (period - 1) + loss) / Decimal(period)

    if avg_loss == 0:
        return Decimal(100)
    if avg_gain == 0:
        return Decimal(0)

    rs = avg_gain / avg_loss
    return HUNDRED - (HUNDRED / (Decimal(1) + rs))
