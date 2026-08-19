from typing import Literal

from pydantic import Field

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.api.schemas.common import MetaSchema, WarningSchema
from stockmon.core.summary import Summary
from stockmon.services.dashboard_service import Dashboard, DashboardStockRow


class DashboardPositionSchema(CamelModel):
    profit_loss: Money
    profit_loss_pct: Money


class DashboardStockSchema(CamelModel):
    ticker: str
    company_name: str
    current_price: Money | None
    # to_camel would produce "change1DPct" (capital D); the contract fixes
    # the field name as "change1dPct" (lowercase d), so it needs an explicit
    # alias override.
    change_1d_pct: Money | None = Field(alias="change1dPct")
    status: Literal["ok", "insufficient_history"]
    suggestion: Literal["BUY", "WAIT", "SELL"] | None
    warning: WarningSchema | None
    position: DashboardPositionSchema | None

    @classmethod
    def from_core(cls, row: DashboardStockRow) -> "DashboardStockSchema":
        return cls(
            ticker=row.ticker,
            company_name=row.company_name,
            current_price=row.current_price,
            change_1d_pct=row.change_1d_pct,
            status=row.status,
            suggestion=row.suggestion_label,
            warning=WarningSchema.from_core(row.warning) if row.warning else None,
            position=(
                DashboardPositionSchema(
                    profit_loss=row.position.profit_loss, profit_loss_pct=row.position.profit_loss_pct
                )
                if row.position
                else None
            ),
        )


class SummarySchema(CamelModel):
    total_invested: Money
    total_current_value: Money
    total_profit_loss: Money
    total_profit_loss_pct: Money

    @classmethod
    def from_core(cls, summary: Summary) -> "SummarySchema":
        return cls(
            total_invested=summary.total_invested,
            total_current_value=summary.total_current_value,
            total_profit_loss=summary.total_profit_loss,
            total_profit_loss_pct=summary.total_profit_loss_pct,
        )


class DashboardResponse(CamelModel):
    meta: MetaSchema
    summary: SummarySchema | None
    stocks: list[DashboardStockSchema]

    @classmethod
    def from_core(cls, meta: MetaSchema, dashboard: Dashboard) -> "DashboardResponse":
        return cls(
            meta=meta,
            summary=SummarySchema.from_core(dashboard.summary) if dashboard.summary else None,
            stocks=[DashboardStockSchema.from_core(row) for row in dashboard.stocks],
        )
