from datetime import date, timedelta
from decimal import Decimal

from stockmon.core.indicators import MIN_HISTORY_DAYS
from stockmon.core.market_data import DailyBar
from stockmon.core.screener import evaluate_screener_bars


def _bar(day: date, close: Decimal, *, volume: int = 1_000_000) -> DailyBar:
    return DailyBar(date=day, open=close, high=close, low=close, close=close, volume=volume)


def _bars_from_closes(closes: list[Decimal], *, start: date = date(2026, 1, 1)) -> list[DailyBar]:
    return [_bar(start + timedelta(days=i), close) for i, close in enumerate(closes)]


def test_ok_status_runs_entry_evaluation_and_sharp_move() -> None:
    # Below 30d avg, near 30d low, low RSI, above-avg volume -> BUY (4/4).
    closes = [Decimal(100)] * (MIN_HISTORY_DAYS - 1) + [Decimal(80)]
    bars = _bars_from_closes(closes)
    evaluation = evaluate_screener_bars(bars)

    assert evaluation.status == "ok"
    assert evaluation.current_price == Decimal(80)
    assert evaluation.suggestion_label == "BUY"
    assert evaluation.conditions_total == 4
    assert evaluation.conditions_met is not None and evaluation.conditions_met >= 3
    assert evaluation.rsi is not None
    assert evaluation.price_vs_30d_avg_pct is not None and evaluation.price_vs_30d_avg_pct < 0
    assert evaluation.sharp_move is True  # >5% 1-day drop
    assert evaluation.change_7d_pct is not None


def test_wait_status_when_fewer_than_3_conditions_pass() -> None:
    closes = [Decimal(100)] * MIN_HISTORY_DAYS
    bars = _bars_from_closes(closes)
    evaluation = evaluate_screener_bars(bars)

    assert evaluation.status == "ok"
    assert evaluation.suggestion_label == "WAIT"
    assert evaluation.sharp_move is False


def test_insufficient_history_with_partial_bars_uses_price_snapshot() -> None:
    bars = _bars_from_closes([Decimal(100), Decimal(105)])
    evaluation = evaluate_screener_bars(bars)

    assert evaluation.status == "insufficient_history"
    assert evaluation.current_price == Decimal(105)
    assert evaluation.change_1d_pct == (Decimal(105) - Decimal(100)) / Decimal(100) * 100
    assert evaluation.suggestion_label is None
    assert evaluation.conditions_met is None
    assert evaluation.conditions_total is None
    assert evaluation.rsi is None
    assert evaluation.price_vs_30d_avg_pct is None
    assert evaluation.sharp_move is None
    assert evaluation.change_7d_pct is None


def test_zero_bars_has_no_price_either() -> None:
    evaluation = evaluate_screener_bars([])

    assert evaluation.status == "insufficient_history"
    assert evaluation.current_price is None
    assert evaluation.change_1d_pct is None
