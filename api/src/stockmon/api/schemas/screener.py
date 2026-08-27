from datetime import datetime
from typing import Literal

from pydantic import Field

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.api.schemas.common import MetaSchema
from stockmon.db.models import ScreenerResult
from stockmon.services.screener_service import ScreenerBatchResult, ScreenerRun


class ScreenerResultSchema(CamelModel):
    ticker: str
    company_name: str
    current_price: Money | None
    # to_camel would produce "change1DPct"; the contract fixes the field
    # name as "change1dPct" (lowercase d), so it needs an explicit alias.
    change_1d_pct: Money | None = Field(alias="change1dPct")
    change_7d_pct: Money | None = Field(alias="change7dPct")
    suggestion: Literal["BUY", "WAIT"] | None
    met_count: int | None
    total_count: int | None
    rsi: Money | None
    # to_camel would produce "priceVs30DAvgPct"; the contract fixes the
    # field name as "priceVs30dAvgPct" (lowercase d), same issue as change1dPct.
    price_vs_30d_avg_pct: Money | None = Field(alias="priceVs30dAvgPct")
    sharp_move: bool | None
    status: Literal["ok", "insufficient_history"]

    @classmethod
    def from_core(cls, row: ScreenerResult) -> "ScreenerResultSchema":
        return cls(
            ticker=row.ticker,
            company_name=row.company_name,
            current_price=row.current_price,
            change_1d_pct=row.change_1d_pct,
            change_7d_pct=row.change_7d_pct,
            suggestion=row.suggestion,  # type: ignore[arg-type]
            met_count=row.conditions_met,
            total_count=row.conditions_total,
            rsi=row.rsi,
            price_vs_30d_avg_pct=row.price_vs_30d_avg_pct,
            sharp_move=row.sharp_move,
            status=row.status,  # type: ignore[arg-type]
        )


class ScreenerResponse(CamelModel):
    meta: MetaSchema
    run_at: datetime | None
    results: list[ScreenerResultSchema]

    @classmethod
    def from_core(cls, meta: MetaSchema, run: ScreenerRun) -> "ScreenerResponse":
        return cls(
            meta=meta,
            run_at=run.run_at,
            results=[ScreenerResultSchema.from_core(row) for row in run.rows],
        )


class ScreenerRefreshFailureSchema(CamelModel):
    ticker: str
    error: str


class ScreenerRefreshResponse(CamelModel):
    refreshed: list[str]
    failed: list[ScreenerRefreshFailureSchema]
    run_at: datetime

    @classmethod
    def from_core(cls, result: ScreenerBatchResult) -> "ScreenerRefreshResponse":
        return cls(
            refreshed=[row.ticker for row in result.rows],
            failed=[ScreenerRefreshFailureSchema(ticker=f.ticker, error=f.error) for f in result.failures],
            run_at=result.run_at,
        )
