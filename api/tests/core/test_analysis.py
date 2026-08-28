from decimal import Decimal

from stockmon.core.analysis import evaluate_analysis_progress


def test_price_below_target_not_reached() -> None:
    progress = evaluate_analysis_progress(Decimal("187.42"), Decimal("210.00"))

    assert progress.target_price == Decimal("210.00")
    assert progress.progress_price == Decimal("187.42")
    assert progress.remaining_price == Decimal("22.58")
    assert progress.reached is False


def test_price_at_or_above_target_is_reached_and_capped() -> None:
    progress = evaluate_analysis_progress(Decimal("314.58"), Decimal("210.00"))

    assert progress.progress_price == Decimal("210.00")  # capped at target for a 0-100% bar
    assert progress.remaining_price == Decimal(0)
    assert progress.reached is True


def test_price_exactly_at_target_is_reached() -> None:
    progress = evaluate_analysis_progress(Decimal("210.00"), Decimal("210.00"))

    assert progress.reached is True
    assert progress.progress_price == Decimal("210.00")
    assert progress.remaining_price == Decimal(0)
