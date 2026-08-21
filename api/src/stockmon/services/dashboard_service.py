from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from stockmon.core.dashboard import sort_dashboard_rows
from stockmon.core.evaluation import Warning
from stockmon.core.money import MoneySummary
from stockmon.core.position import PositionValue
from stockmon.core.summary import Summary, build_summary
from stockmon.db.models import Stock
from stockmon.services.money_service import build_money_summary, has_money_activity
from stockmon.services.settings_service import get_effective_target
from stockmon.services.stock_service import Status, evaluate_stock_snapshot


@dataclass(frozen=True)
class DashboardStockRow:
    ticker: str
    company_name: str
    current_price: Decimal | None
    change_1d_pct: Decimal | None
    status: Status
    suggestion_label: Literal["BUY", "WAIT", "SELL"] | None
    warning: Warning | None
    position: PositionValue | None

    @property
    def has_warning(self) -> bool:
        return self.warning is not None


@dataclass(frozen=True)
class Dashboard:
    stocks: list[DashboardStockRow]
    summary: Summary | None
    money: MoneySummary | None


def build_dashboard(db: Session) -> Dashboard:
    rows: list[DashboardStockRow] = []
    invested: list[Decimal] = []
    current_values: list[Decimal] = []
    open_position_pnls: list[Decimal] = []

    for stock in db.query(Stock).all():
        target = get_effective_target(db, stock.id)
        evaluation = evaluate_stock_snapshot(db, stock, target)

        rows.append(
            DashboardStockRow(
                ticker=stock.ticker,
                company_name=stock.company_name,
                current_price=evaluation.current_price,
                change_1d_pct=evaluation.change_1d_pct,
                status=evaluation.status,
                suggestion_label=evaluation.suggestion.label if evaluation.suggestion else None,
                warning=evaluation.warning,
                position=evaluation.position_value,
            )
        )

        if evaluation.position is not None and evaluation.position_value is not None:
            invested.append(evaluation.position.amount_invested)
            current_values.append(evaluation.position_value.current_value)
            open_position_pnls.append(evaluation.position_value.profit_loss)

    return Dashboard(
        stocks=sort_dashboard_rows(rows),
        summary=build_summary(invested, current_values),
        money=build_money_summary(db, open_position_pnls) if has_money_activity(db) else None,
    )
