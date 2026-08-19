from datetime import date
from decimal import Decimal
from typing import Literal

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.services.trade_service import TradeResult


class TradeRequest(CamelModel):
    ticker: str
    action: Literal["buy", "sell"]
    shares: Decimal
    price_per_share: Decimal
    date: date


class TradeItemSchema(CamelModel):
    id: int
    ticker: str
    action: Literal["buy", "sell"]
    shares: Money
    price_per_share: Money
    date: date


class UpdatedPositionSchema(CamelModel):
    ticker: str
    shares_held: Money
    avg_purchase_price: Money
    amount_invested: Money


class TradeResponse(CamelModel):
    trade: TradeItemSchema
    updated_position: UpdatedPositionSchema | None

    @classmethod
    def from_core(cls, ticker: str, result: TradeResult) -> "TradeResponse":
        trade = result.trade
        updated_position = None
        if result.updated_position is not None:
            updated_position = UpdatedPositionSchema(
                ticker=ticker,
                shares_held=result.updated_position.shares_held,
                avg_purchase_price=result.updated_position.avg_purchase_price,
                amount_invested=result.updated_position.amount_invested,
            )
        return cls(
            trade=TradeItemSchema(
                id=trade.id,
                ticker=ticker,
                action=trade.action,
                shares=trade.shares,
                price_per_share=trade.price_per_share,
                date=trade.trade_date,
            ),
            updated_position=updated_position,
        )


class ErrorResponse(CamelModel):
    error: str
