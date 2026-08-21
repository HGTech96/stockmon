from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.money import MoneySummary
from stockmon.core.position import Position, PositionValue, ProfitTargetProgress, evaluate_profit_target
from stockmon.core.summary import Summary, build_summary
from stockmon.db.models import Stock, Trade
from stockmon.services.money_service import build_money_summary, has_money_activity
from stockmon.services.settings_service import get_effective_target
from stockmon.services.stock_service import Status, evaluate_stock_snapshot


@dataclass(frozen=True)
class PortfolioPosition:
    ticker: str
    company_name: str
    position: Position
    position_value: PositionValue
    profit_target: ProfitTargetProgress
    status: Status
    suggestion_label: Literal["BUY", "WAIT", "SELL"] | None


@dataclass(frozen=True)
class Portfolio:
    has_trades: bool
    summary: Summary | None
    money: MoneySummary | None
    positions: list[PortfolioPosition]
    watchlist: list[str]


def get_portfolio(db: Session) -> Portfolio:
    stocks = db.query(Stock).order_by(Stock.id).all()
    watchlist = [stock.ticker for stock in stocks]
    has_trades = db.query(Trade.id).first() is not None

    positions: list[PortfolioPosition] = []
    invested: list[Decimal] = []
    current_values: list[Decimal] = []
    open_position_pnls: list[Decimal] = []

    for stock in stocks:
        target = get_effective_target(db, stock.id)
        evaluation = evaluate_stock_snapshot(db, stock, target)
        if evaluation.position is None or evaluation.position_value is None:
            continue

        positions.append(
            PortfolioPosition(
                ticker=stock.ticker,
                company_name=stock.company_name,
                position=evaluation.position,
                position_value=evaluation.position_value,
                profit_target=evaluate_profit_target(evaluation.position_value.profit_loss, target),
                status=evaluation.status,
                suggestion_label=evaluation.suggestion.label if evaluation.suggestion else None,
            )
        )
        invested.append(evaluation.position.amount_invested)
        current_values.append(evaluation.position_value.current_value)
        open_position_pnls.append(evaluation.position_value.profit_loss)

    return Portfolio(
        has_trades=has_trades,
        summary=build_summary(invested, current_values) if has_trades else None,
        money=build_money_summary(db, open_position_pnls) if has_money_activity(db) else None,
        positions=positions,
        watchlist=watchlist,
    )
