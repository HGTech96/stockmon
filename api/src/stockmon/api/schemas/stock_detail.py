from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.api.schemas.common import MetaSchema, ProfitTargetSchema, SuggestionSchema, WarningSchema
from stockmon.core.analysis import AnalysisProgress
from stockmon.core.indicators import Indicators
from stockmon.services.stock_detail_service import ChartDay, NewsLinks, StockDetail
from stockmon.services.stock_service import AnalysisView


class ChartDaySchema(CamelModel):
    date: date
    close: Money
    volume: int

    @classmethod
    def from_core(cls, day: ChartDay) -> "ChartDaySchema":
        return cls(date=day.date, close=day.close, volume=day.volume)


class ChartSchema(CamelModel):
    days: list[ChartDaySchema]
    thirty_day_average: Money
    user_avg_purchase_price: Money | None


class IndicatorsSchema(CamelModel):
    current_price: Money
    # to_camel would produce "change1DPct"/"change7DPct" (capital letter);
    # the contract fixes these as lowercase, so they need explicit aliases.
    change_1d_pct: Money = Field(alias="change1dPct")
    change_7d_pct: Money = Field(alias="change7dPct")
    thirty_day_average: Money
    thirty_day_high: Money
    thirty_day_low: Money
    distance_from_high_pct: Money
    distance_from_low_pct: Money
    rsi: Money
    todays_volume: int
    average_volume: Money
    volume_vs_average_pct: Money

    @classmethod
    def from_core(cls, indicators: Indicators) -> "IndicatorsSchema":
        return cls(
            current_price=indicators.current_price,
            change_1d_pct=indicators.change_1d_pct,
            change_7d_pct=indicators.change_7d_pct,
            thirty_day_average=indicators.thirty_day_average,
            thirty_day_high=indicators.thirty_day_high,
            thirty_day_low=indicators.thirty_day_low,
            distance_from_high_pct=indicators.distance_from_high_pct,
            distance_from_low_pct=indicators.distance_from_low_pct,
            rsi=indicators.rsi,
            todays_volume=indicators.todays_volume,
            average_volume=indicators.average_volume,
            volume_vs_average_pct=indicators.volume_vs_average_pct,
        )


class DetailPositionSchema(CamelModel):
    shares_held: Money
    avg_purchase_price: Money
    amount_invested: Money
    current_value: Money
    profit_loss: Money
    profit_loss_pct: Money
    profit_target: ProfitTargetSchema


class AnalysisSchema(CamelModel):
    date: date | None
    value: Money | None

    @classmethod
    def from_core(cls, view: AnalysisView) -> "AnalysisSchema":
        return cls(date=view.date, value=view.value)


class SetAnalysisRequest(CamelModel):
    date: date
    value: Decimal


class AnalysisProgressSchema(CamelModel):
    target_price: Money
    progress_price: Money
    remaining_price: Money
    reached: bool

    @classmethod
    def from_core(cls, progress: AnalysisProgress) -> "AnalysisProgressSchema":
        return cls(
            target_price=progress.target_price,
            progress_price=progress.progress_price,
            remaining_price=progress.remaining_price,
            reached=progress.reached,
        )


class DetailAnalysisSchema(CamelModel):
    date: date | None
    value: Money | None
    progress: AnalysisProgressSchema | None

    @classmethod
    def from_core(cls, view: AnalysisView, progress: AnalysisProgress | None) -> "DetailAnalysisSchema":
        return cls(
            date=view.date,
            value=view.value,
            progress=AnalysisProgressSchema.from_core(progress) if progress else None,
        )


class NewsLinksSchema(CamelModel):
    cnn_finance: str
    yahoo_finance: str
    google_finance: str
    investor_relations: str | None

    @classmethod
    def from_core(cls, links: NewsLinks) -> "NewsLinksSchema":
        return cls(
            cnn_finance=links.cnn_finance,
            yahoo_finance=links.yahoo_finance,
            google_finance=links.google_finance,
            investor_relations=links.investor_relations,
        )


class StockDetailResponse(CamelModel):
    meta: MetaSchema
    ticker: str
    company_name: str
    current_price: Money | None
    change_1d_pct: Money | None = Field(alias="change1dPct")
    status: Literal["ok", "insufficient_history"]
    days_of_history_available: int
    days_of_history_required: int
    trading_days_until_ready: int | None
    suggestion: SuggestionSchema | None
    warning: WarningSchema | None
    chart: ChartSchema | None
    indicators: IndicatorsSchema | None
    position: DetailPositionSchema | None
    analysis: DetailAnalysisSchema | None
    news_links: NewsLinksSchema

    @classmethod
    def from_core(cls, meta: MetaSchema, detail: StockDetail) -> "StockDetailResponse":
        evaluation = detail.evaluation
        stock = evaluation.stock

        chart = None
        if detail.chart_days is not None:
            assert detail.thirty_day_average is not None
            chart = ChartSchema(
                days=[ChartDaySchema.from_core(day) for day in detail.chart_days],
                thirty_day_average=detail.thirty_day_average,
                user_avg_purchase_price=detail.user_avg_purchase_price,
            )

        position = None
        if evaluation.position is not None and evaluation.position_value is not None:
            assert detail.profit_target is not None
            position = DetailPositionSchema(
                shares_held=evaluation.position.shares_held,
                avg_purchase_price=evaluation.position.avg_purchase_price,
                amount_invested=evaluation.position.amount_invested,
                current_value=evaluation.position_value.current_value,
                profit_loss=evaluation.position_value.profit_loss,
                profit_loss_pct=evaluation.position_value.profit_loss_pct,
                profit_target=ProfitTargetSchema.from_core(detail.profit_target),
            )

        return cls(
            meta=meta,
            ticker=stock.ticker,
            company_name=stock.company_name,
            current_price=evaluation.current_price,
            change_1d_pct=evaluation.change_1d_pct,
            status=evaluation.status,
            days_of_history_available=evaluation.days_available,
            days_of_history_required=detail.days_required,
            trading_days_until_ready=detail.trading_days_until_ready,
            suggestion=SuggestionSchema.from_core(evaluation.suggestion) if evaluation.suggestion else None,
            warning=WarningSchema.from_core(evaluation.warning) if evaluation.warning else None,
            chart=chart,
            indicators=IndicatorsSchema.from_core(evaluation.indicators) if evaluation.indicators else None,
            position=position,
            analysis=DetailAnalysisSchema.from_core(detail.analysis, detail.analysis_progress) if detail.analysis else None,
            news_links=NewsLinksSchema.from_core(detail.news_links),
        )
