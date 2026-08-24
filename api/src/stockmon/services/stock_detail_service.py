from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from stockmon.core.indicators import MIN_HISTORY_DAYS
from stockmon.core.position import ProfitTargetProgress, evaluate_profit_target
from stockmon.db.models import Stock
from stockmon.services.settings_service import get_effective_target
from stockmon.services.stock_service import StockEvaluation, StockNotFoundError, evaluate_stock_snapshot


@dataclass(frozen=True)
class ChartDay:
    date: date
    close: Decimal
    volume: int


@dataclass(frozen=True)
class NewsLinks:
    yahoo_finance: str
    google_finance: str
    investor_relations: str | None


@dataclass(frozen=True)
class StockDetail:
    evaluation: StockEvaluation
    days_required: int
    trading_days_until_ready: int | None
    chart_days: list[ChartDay] | None
    thirty_day_average: Decimal | None
    user_avg_purchase_price: Decimal | None
    profit_target: ProfitTargetProgress | None
    effective_target_dollars: Decimal
    news_links: NewsLinks


def news_links_for_ticker(ticker: str, investor_relations_url: str | None) -> NewsLinks:
    return NewsLinks(
        yahoo_finance=f"https://finance.yahoo.com/quote/{ticker}",
        google_finance=f"https://www.google.com/finance/quote/{ticker}",
        investor_relations=investor_relations_url,
    )


def get_stock_detail(db: Session, ticker: str) -> StockDetail:
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if stock is None:
        raise StockNotFoundError(ticker)

    target = get_effective_target(db, stock.id)
    evaluation = evaluate_stock_snapshot(db, stock, target)

    chart_days: list[ChartDay] | None = None
    thirty_day_average: Decimal | None = None
    trading_days_until_ready: int | None = None

    if evaluation.status == "ok":
        window = evaluation.bars[-MIN_HISTORY_DAYS:]
        chart_days = [ChartDay(date=bar.date, close=bar.close, volume=bar.volume) for bar in window]
        assert evaluation.indicators is not None
        thirty_day_average = evaluation.indicators.thirty_day_average
    else:
        trading_days_until_ready = MIN_HISTORY_DAYS - evaluation.days_available

    profit_target: ProfitTargetProgress | None = None
    if evaluation.position_value is not None:
        profit_target = evaluate_profit_target(evaluation.position_value.profit_loss, target)

    return StockDetail(
        evaluation=evaluation,
        days_required=MIN_HISTORY_DAYS,
        trading_days_until_ready=trading_days_until_ready,
        chart_days=chart_days,
        thirty_day_average=thirty_day_average,
        user_avg_purchase_price=evaluation.position.avg_purchase_price if evaluation.position else None,
        profit_target=profit_target,
        effective_target_dollars=target,
        news_links=news_links_for_ticker(stock.ticker, stock.investor_relations_url),
    )
