from typing import Literal

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.api.schemas.common import MetaSchema, ProfitTargetSchema
from stockmon.api.schemas.dashboard import SummarySchema
from stockmon.services.portfolio_service import Portfolio, PortfolioPosition


class PortfolioPositionSchema(CamelModel):
    ticker: str
    company_name: str
    shares_held: Money
    avg_purchase_price: Money
    amount_invested: Money
    current_value: Money
    profit_loss: Money
    profit_loss_pct: Money
    profit_target: ProfitTargetSchema
    status: Literal["ok", "insufficient_history"]
    suggestion: Literal["BUY", "WAIT", "SELL"] | None

    @classmethod
    def from_core(cls, position: PortfolioPosition) -> "PortfolioPositionSchema":
        return cls(
            ticker=position.ticker,
            company_name=position.company_name,
            shares_held=position.position.shares_held,
            avg_purchase_price=position.position.avg_purchase_price,
            amount_invested=position.position.amount_invested,
            current_value=position.position_value.current_value,
            profit_loss=position.position_value.profit_loss,
            profit_loss_pct=position.position_value.profit_loss_pct,
            profit_target=ProfitTargetSchema.from_core(position.profit_target),
            status=position.status,
            suggestion=position.suggestion_label,
        )


class PortfolioResponse(CamelModel):
    meta: MetaSchema
    has_trades: bool
    summary: SummarySchema | None
    positions: list[PortfolioPositionSchema]
    watchlist: list[str]

    @classmethod
    def from_core(cls, meta: MetaSchema, portfolio: Portfolio) -> "PortfolioResponse":
        return cls(
            meta=meta,
            has_trades=portfolio.has_trades,
            summary=SummarySchema.from_core(portfolio.summary) if portfolio.summary else None,
            positions=[PortfolioPositionSchema.from_core(p) for p in portfolio.positions],
            watchlist=portfolio.watchlist,
        )
