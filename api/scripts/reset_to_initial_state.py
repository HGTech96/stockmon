"""Reset the DB to its initial state: stock-related data (stocks, price
history) stays untouched; trades and cash events are wiped, so there's no
portfolio, no trade history, and no cash balance.

Positions and the portfolio are derived from the trades table (event-sourced,
see CLAUDE.md), so deleting trades is sufficient to clear the portfolio --
there is no separate positions table to reset.
"""

from stockmon.db.base import SessionLocal
from stockmon.db.models import CashEvent, Trade


def reset() -> None:
    db = SessionLocal()
    try:
        trades_deleted = db.query(Trade).delete()
        cash_events_deleted = db.query(CashEvent).delete()
        db.commit()
        print(f"Deleted {trades_deleted} trades")
        print(f"Deleted {cash_events_deleted} cash events")
        print("Stocks and price history left untouched.")
    finally:
        db.close()


if __name__ == "__main__":
    reset()
