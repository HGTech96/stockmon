from datetime import date, timedelta
from decimal import Decimal

import pytest

from stockmon.core.indicators import (
    MIN_HISTORY_DAYS,
    RSI_PERIOD,
    InsufficientHistoryError,
    _wilder_rsi,
    calculate_indicators,
    calculate_price_snapshot,
    price_vs_30d_avg_pct,
)
from stockmon.core.market_data import DailyBar


def _bar(day: date, close: Decimal, *, high: Decimal | None = None,
         low: Decimal | None = None, volume: int = 1_000_000) -> DailyBar:
    return DailyBar(
        date=day,
        open=close,
        high=high if high is not None else close,
        low=low if low is not None else close,
        close=close,
        volume=volume,
    )


def _bars_from_closes(closes: list[Decimal], *, start: date = date(2026, 1, 1),
                       volumes: list[int] | None = None) -> list[DailyBar]:
    volumes = volumes or [1_000_000] * len(closes)
    return [
        _bar(start + timedelta(days=i), close, volume=volumes[i])
        for i, close in enumerate(closes)
    ]


def test_insufficient_history_raises() -> None:
    bars = _bars_from_closes([Decimal(100)] * (MIN_HISTORY_DAYS - 1))
    with pytest.raises(InsufficientHistoryError) as exc_info:
        calculate_indicators(bars)
    assert exc_info.value.available == MIN_HISTORY_DAYS - 1
    assert exc_info.value.required == MIN_HISTORY_DAYS


def test_change_1d_and_7d_pct() -> None:
    closes = (
        [Decimal(100)] * 22
        + [Decimal(110), Decimal(111), Decimal(112), Decimal(113),
           Decimal(114), Decimal(115), Decimal(116), Decimal(120)]
    )
    bars = _bars_from_closes(closes)
    indicators = calculate_indicators(bars)
    assert indicators.current_price == Decimal(120)
    assert indicators.change_1d_pct == (Decimal(120) - Decimal(116)) / Decimal(116) * 100
    assert indicators.change_7d_pct == (Decimal(120) - Decimal(110)) / Decimal(110) * 100


def test_thirty_day_avg_high_low_and_distances() -> None:
    closes = [Decimal(90)] + [Decimal(100)] * 28 + [Decimal(110)]
    bars = _bars_from_closes(closes)
    indicators = calculate_indicators(bars)
    assert indicators.thirty_day_high == Decimal(110)
    assert indicators.thirty_day_low == Decimal(90)
    assert indicators.distance_from_high_pct == Decimal(0)
    assert indicators.distance_from_low_pct == (Decimal(110) - Decimal(90)) / Decimal(90) * 100
    expected_avg = (Decimal(90) + Decimal(100) * 28 + Decimal(110)) / Decimal(30)
    assert indicators.thirty_day_average == expected_avg


def test_volume_vs_average() -> None:
    closes = [Decimal(100)] * 30
    volumes = [1000] * 29 + [2000]
    bars = _bars_from_closes(closes, volumes=volumes)
    indicators = calculate_indicators(bars)
    assert indicators.todays_volume == 2000
    expected_avg_volume = (Decimal(1000) * 29 + Decimal(2000)) / Decimal(30)
    assert indicators.average_volume == expected_avg_volume
    assert indicators.volume_vs_average_pct == Decimal(2000) / expected_avg_volume * 100


def test_zero_average_volume_does_not_crash() -> None:
    closes = [Decimal(100)] * 30
    volumes = [0] * 30
    bars = _bars_from_closes(closes, volumes=volumes)
    indicators = calculate_indicators(bars)
    assert indicators.average_volume == Decimal(0)
    assert indicators.volume_vs_average_pct == Decimal(0)


def test_zero_volume_today_with_nonzero_average() -> None:
    closes = [Decimal(100)] * 30
    volumes = [1000] * 29 + [0]
    bars = _bars_from_closes(closes, volumes=volumes)
    indicators = calculate_indicators(bars)
    assert indicators.todays_volume == 0
    assert indicators.volume_vs_average_pct == Decimal(0)


def test_wilder_rsi_hand_computed_example() -> None:
    # Classic 15-close reference series (14 deltas -> seed average only, no
    # smoothing iterations), used to lock the exact Wilder RSI formula.
    closes = [
        Decimal(str(c)) for c in [
            44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42,
            45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.28,
        ]
    ]
    rsi = _wilder_rsi(closes)
    assert abs(rsi - Decimal("70.4641")) < Decimal("0.01")


def test_wilder_rsi_all_gains_is_100() -> None:
    closes = [Decimal(100 + i) for i in range(RSI_PERIOD + 1)]
    assert _wilder_rsi(closes) == Decimal(100)


def test_wilder_rsi_all_losses_is_0() -> None:
    closes = [Decimal(100 - i) for i in range(RSI_PERIOD + 1)]
    assert _wilder_rsi(closes) == Decimal(0)


def test_wilder_rsi_insufficient_data_raises() -> None:
    closes = [Decimal(100)] * RSI_PERIOD
    with pytest.raises(InsufficientHistoryError):
        _wilder_rsi(closes)


def test_calculate_indicators_rsi_uses_full_history_not_just_30_days() -> None:
    closes = [Decimal(100) + Decimal(i) * Decimal("0.3") for i in range(45)]
    bars = _bars_from_closes(closes)
    indicators = calculate_indicators(bars)
    assert indicators.rsi == _wilder_rsi(closes)


def test_price_snapshot_empty_bars_is_none() -> None:
    assert calculate_price_snapshot([]) is None


def test_price_snapshot_single_bar_has_zero_change() -> None:
    bars = _bars_from_closes([Decimal(100)])
    snapshot = calculate_price_snapshot(bars)
    assert snapshot is not None
    assert snapshot.current_price == Decimal(100)
    assert snapshot.change_1d_pct == Decimal(0)


def test_price_snapshot_uses_last_two_bars() -> None:
    bars = _bars_from_closes([Decimal(100), Decimal(90), Decimal(99)])
    snapshot = calculate_price_snapshot(bars)
    assert snapshot is not None
    assert snapshot.current_price == Decimal(99)
    assert snapshot.change_1d_pct == (Decimal(99) - Decimal(90)) / Decimal(90) * 100


def test_price_vs_30d_avg_pct() -> None:
    closes = [Decimal(90)] + [Decimal(100)] * 28 + [Decimal(110)]
    bars = _bars_from_closes(closes)
    indicators = calculate_indicators(bars)
    expected_avg = (Decimal(90) + Decimal(100) * 28 + Decimal(110)) / Decimal(30)
    assert price_vs_30d_avg_pct(indicators) == (Decimal(110) - expected_avg) / expected_avg * 100
