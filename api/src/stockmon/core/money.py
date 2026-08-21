from dataclasses import dataclass
from decimal import Decimal

from stockmon.core.cash import CashFlowEvent, chronological_key, derive_cash_balance


@dataclass(frozen=True)
class MoneySummary:
    cash_available: Decimal
    net_deposited: Decimal
    realized_earned: Decimal
    realized_lost: Decimal
    unrealized_gain_open: Decimal
    unrealized_loss_open: Decimal


def compute_money_summary(
    cash_flow_events: list[CashFlowEvent],
    realized_pnls: list[Decimal],
    open_position_pnls: list[Decimal],
) -> MoneySummary:
    """cash_available reuses derive_cash_balance (the one source of truth for
    the cash-replay rule) rather than re-summing independently, non-strict
    since this is a display path -- it must never raise on a GET, the
    never-negative invariant is enforced at write time (see
    cash_service.validate_cash_sequence), not here. The other five figures
    are simple sign-split sums of the two input lists (loss/lost returned as
    positive numbers)."""
    cash_available = derive_cash_balance(sorted(cash_flow_events, key=chronological_key), strict=False)

    net_deposited = sum(
        (
            event.amount if event.kind == "deposit" else -event.amount
            for event in cash_flow_events
            if event.kind in ("deposit", "withdraw")
        ),
        Decimal(0),
    )

    realized_earned = sum((pnl for pnl in realized_pnls if pnl > 0), Decimal(0))
    realized_lost = -sum((pnl for pnl in realized_pnls if pnl < 0), Decimal(0))
    unrealized_gain_open = sum((pnl for pnl in open_position_pnls if pnl > 0), Decimal(0))
    unrealized_loss_open = -sum((pnl for pnl in open_position_pnls if pnl < 0), Decimal(0))

    return MoneySummary(
        cash_available=cash_available,
        net_deposited=net_deposited,
        realized_earned=realized_earned,
        realized_lost=realized_lost,
        unrealized_gain_open=unrealized_gain_open,
        unrealized_loss_open=unrealized_loss_open,
    )
