from dataclasses import dataclass
from decimal import Decimal

HUNDRED = Decimal(100)


@dataclass(frozen=True)
class Summary:
    total_invested: Decimal
    total_current_value: Decimal
    total_profit_loss: Decimal
    total_profit_loss_pct: Decimal


def build_summary(invested: list[Decimal], current_values: list[Decimal]) -> Summary | None:
    """None when there are no valued positions to aggregate. `invested` and
    `current_values` must be parallel lists (one entry per open position)."""
    if not invested:
        return None
    total_invested = sum(invested, Decimal(0))
    total_current_value = sum(current_values, Decimal(0))
    total_profit_loss = total_current_value - total_invested
    total_profit_loss_pct = (
        Decimal(0) if total_invested == 0 else total_profit_loss / total_invested * HUNDRED
    )
    return Summary(
        total_invested=total_invested,
        total_current_value=total_current_value,
        total_profit_loss=total_profit_loss,
        total_profit_loss_pct=total_profit_loss_pct,
    )
