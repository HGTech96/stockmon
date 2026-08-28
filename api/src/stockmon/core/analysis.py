from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AnalysisProgress:
    target_price: Decimal
    progress_price: Decimal
    remaining_price: Decimal
    reached: bool


def evaluate_analysis_progress(current_price: Decimal, target_price: Decimal) -> AnalysisProgress:
    """progress_price is current_price clamped to [0, target_price] (for a
    0-100% progress bar); remaining_price is uncapped above target_price so a
    price still below the analyzed value shows how far it is from it,
    floored at 0. Mirrors evaluate_profit_target's shape."""
    reached = current_price >= target_price
    progress_price = min(max(current_price, Decimal(0)), target_price)
    remaining_price = max(target_price - current_price, Decimal(0))
    return AnalysisProgress(
        target_price=target_price,
        progress_price=progress_price,
        remaining_price=remaining_price,
        reached=reached,
    )
