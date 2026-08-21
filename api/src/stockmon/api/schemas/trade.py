from datetime import date
from decimal import Decimal
from typing import Literal

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.api.schemas.common import MetaSchema
from stockmon.services.trade_service import TradeHistoryEntry, TradeResult


class TradeRequest(CamelModel):
    ticker: str
    action: Literal["buy", "sell"]
    shares: Decimal
    price_per_share: Decimal
    date: date


class TradeUpdateRequest(CamelModel):
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


class TradeHistoryEntrySchema(CamelModel):
    id: int
    ticker: str
    company_name: str
    action: Literal["buy", "sell"]
    shares: Money
    price_per_share: Money
    total_usd: Money
    realized_pnl_usd: Money | None
    date: date

    @classmethod
    def from_core(cls, entry: TradeHistoryEntry) -> "TradeHistoryEntrySchema":
        return cls(
            id=entry.id,
            ticker=entry.ticker,
            company_name=entry.company_name,
            action=entry.action,
            shares=entry.shares,
            price_per_share=entry.price_per_share,
            total_usd=entry.total_usd,
            realized_pnl_usd=entry.realized_pnl_usd,
            date=entry.date,
        )


class TradeHistoryResponse(CamelModel):
    meta: MetaSchema
    trades: list[TradeHistoryEntrySchema]

    @classmethod
    def from_core(cls, meta: MetaSchema, entries: list[TradeHistoryEntry]) -> "TradeHistoryResponse":
        return cls(meta=meta, trades=[TradeHistoryEntrySchema.from_core(e) for e in entries])


class ErrorResponse(CamelModel):
    error: str
