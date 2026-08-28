from datetime import date, datetime
from decimal import Decimal

from stockmon.core.market_data import DailyBar, Quote, merge_live_quote


def _bar(day: date, close: Decimal) -> DailyBar:
    return DailyBar(date=day, open=close, high=close, low=close, close=close, volume=1_000_000)


def test_merge_live_quote_replaces_close_on_same_day() -> None:
    bars = [_bar(date(2026, 8, 26), Decimal("100.00")), _bar(date(2026, 8, 27), Decimal("101.00"))]
    quote = Quote(price=Decimal("103.50"), as_of=datetime(2026, 8, 27, 14, 30))

    result = merge_live_quote(bars, quote)

    assert result[-1].close == Decimal("103.50")
    assert result[-1].date == date(2026, 8, 27)
    assert result[:-1] == bars[:-1]


def test_merge_live_quote_noop_when_last_bar_not_quotes_day() -> None:
    bars = [_bar(date(2026, 8, 26), Decimal("100.00"))]
    quote = Quote(price=Decimal("103.50"), as_of=datetime(2026, 8, 27, 14, 30))

    result = merge_live_quote(bars, quote)

    assert result == bars


def test_merge_live_quote_noop_on_empty_bars() -> None:
    quote = Quote(price=Decimal("103.50"), as_of=datetime(2026, 8, 27, 14, 30))

    assert merge_live_quote([], quote) == []


def test_merge_live_quote_preserves_other_fields_of_replaced_bar() -> None:
    bars = [_bar(date(2026, 8, 27), Decimal("100.00"))]
    bars[0] = DailyBar(
        date=date(2026, 8, 27), open=Decimal("99.00"), high=Decimal("102.00"),
        low=Decimal("98.50"), close=Decimal("100.00"), volume=2_000_000,
    )
    quote = Quote(price=Decimal("101.75"), as_of=datetime(2026, 8, 27, 10, 0))

    result = merge_live_quote(bars, quote)

    assert result[-1].close == Decimal("101.75")
    assert result[-1].open == Decimal("99.00")
    assert result[-1].high == Decimal("102.00")
    assert result[-1].low == Decimal("98.50")
    assert result[-1].volume == 2_000_000
