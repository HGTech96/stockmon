from decimal import Decimal

from sqlalchemy.orm import Session

from stockmon.core.money import MoneySummary, compute_money_summary
from stockmon.db.models import CashEvent, Trade, WatchlistEntry
from stockmon.services.cash_service import load_all_cash_event_flow_events, load_all_trade_flow_events
from stockmon.services.trade_service import list_trade_history


def has_money_activity(db: Session, user_id: int) -> bool:
    """True if this user has any cash_events row OR any trades row at all.
    Drives whether `money` renders -- present whenever there's any cash or
    trade activity, independent of `hasTrades`/`summary` (a deposit with
    zero trades is a valid, important state that must still show up)."""
    has_cash = db.query(CashEvent.id).filter(CashEvent.user_id == user_id).first() is not None
    has_trades = (
        db.query(Trade.id)
        .join(WatchlistEntry, Trade.watchlist_entry_id == WatchlistEntry.id)
        .filter(WatchlistEntry.user_id == user_id)
        .first()
        is not None
    )
    return has_cash or has_trades


def build_money_summary(db: Session, user_id: int, open_position_pnls: list[Decimal]) -> MoneySummary:
    """Gathers this user's cash_flow_events (trades + cash log) and
    realized_pnls (reused from trade_service.list_trade_history's existing
    per-sell realizedPnlUsd, not recomputed). open_position_pnls is passed
    in by the caller (dashboard_service / portfolio_service), which already
    computed PositionValue.profit_loss per open position in its own loop."""
    cash_flow_events = load_all_trade_flow_events(db, user_id) + load_all_cash_event_flow_events(db, user_id)
    realized_pnls = [
        entry.realized_pnl_usd for entry in list_trade_history(db, user_id) if entry.realized_pnl_usd is not None
    ]
    return compute_money_summary(cash_flow_events, realized_pnls, open_position_pnls)
