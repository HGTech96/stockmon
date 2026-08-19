from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

HUNDRED = Decimal(100)


class PositionError(Exception):
    """Raised when a sell exceeds the shares held at that point in the trade history."""


@dataclass(frozen=True)
class TradeEvent:
    action: Literal["buy", "sell"]
    shares: Decimal
    price_per_share: Decimal
    date: date


@dataclass(frozen=True)
class Position:
    shares_held: Decimal
    avg_purchase_price: Decimal
    amount_invested: Decimal


@dataclass(frozen=True)
class PositionValue:
    current_value: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal


@dataclass(frozen=True)
class ProfitTargetProgress:
    target_dollars: Decimal
    progress_dollars: Decimal
    remaining_dollars: Decimal
    reached: bool


def derive_position(trades: list[TradeEvent]) -> Position | None:
    """Replays trades in the given order (caller sorts chronologically) using
    the weighted-average-cost rule. Returns None if net shares held is 0
    (never opened, or fully closed by sells)."""
    shares = Decimal(0)
    avg_price = Decimal(0)
    invested = Decimal(0)

    for trade in trades:
        if trade.action == "buy":
            invested += trade.shares * trade.price_per_share
            shares += trade.shares
            avg_price = invested / shares
        else:
            if trade.shares > shares:
                raise PositionError(
                    f"cannot sell {trade.shares} shares on {trade.date}, only {shares} held"
                )
            proportion = trade.shares / shares
            invested -= invested * proportion
            shares -= trade.shares

    if shares == 0:
        return None
    return Position(shares_held=shares, avg_purchase_price=avg_price, amount_invested=invested)


def value_position(position: Position, current_price: Decimal) -> PositionValue:
    current_value = position.shares_held * current_price
    profit_loss = current_value - position.amount_invested
    if position.amount_invested == 0:
        profit_loss_pct = Decimal(0)
    else:
        profit_loss_pct = profit_loss / position.amount_invested * HUNDRED
    return PositionValue(
        current_value=current_value,
        profit_loss=profit_loss,
        profit_loss_pct=profit_loss_pct,
    )


def evaluate_profit_target(profit_loss: Decimal, target_dollars: Decimal) -> ProfitTargetProgress:
    """progress_dollars is profit_loss clamped to [0, target_dollars] (for a
    0-100% progress bar); remaining_dollars is uncapped above target_dollars
    so a losing position shows how far it is from the target, floored at 0."""
    reached = profit_loss >= target_dollars
    progress_dollars = min(max(profit_loss, Decimal(0)), target_dollars)
    remaining_dollars = max(target_dollars - profit_loss, Decimal(0))
    return ProfitTargetProgress(
        target_dollars=target_dollars,
        progress_dollars=progress_dollars,
        remaining_dollars=remaining_dollars,
        reached=reached,
    )
