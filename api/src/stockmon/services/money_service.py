from decimal import Decimal

from sqlalchemy.orm import Session

from stockmon.core.money import MoneySummary, compute_money_summary
from stockmon.db.models import CashEvent, Trade
from stockmon.services.cash_service import load_all_cash_event_flow_events, load_all_trade_flow_events
from stockmon.services.trade_service import list_trade_history


def has_money_activity(db: Session) -> bool:
    """True if any cash_events row OR any trades row exists at all. Drives
    whether `money` renders -- present whenever there's any cash or trade
    activity, independent of `hasTrades`/`summary` (a deposit with zero
    trades is a valid, important state that must still show up)."""
    return db.query(CashEvent.id).first() is not None or db.query(Trade.id).first() is not None


def build_money_summary(db: Session, open_position_pnls: list[Decimal]) -> MoneySummary:
    """Gathers cash_flow_events (trades + cash log) and realized_pnls (reused
    from trade_service.list_trade_history's existing per-sell
    realizedPnlUsd, not recomputed). open_position_pnls is passed in by the
    caller (dashboard_service / portfolio_service), which already computed
    PositionValue.profit_loss per open position in its own loop."""
    cash_flow_events = load_all_trade_flow_events(db) + load_all_cash_event_flow_events(db)
    realized_pnls = [entry.realized_pnl_usd for entry in list_trade_history(db) if entry.realized_pnl_usd is not None]
    return compute_money_summary(cash_flow_events, realized_pnls, open_position_pnls)
