"""Reset one user's data to its initial state: stock-related data
(tickers, price history -- both shared across users) stays untouched;
that user's trades and cash events are wiped, so their portfolio, trade
history, and cash balance are all empty. Other users' data is unaffected.

Positions and the portfolio are derived from the trades table (event-sourced,
see CLAUDE.md), so deleting trades is sufficient to clear the portfolio --
there is no separate positions table to reset.

Usage: python scripts/reset_to_initial_state.py <username>
"""

import sys

from stockmon.db.base import SessionLocal
from stockmon.db.models import CashEvent, Trade, User, WatchlistEntry


def reset(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            print(f"No user '{username}'")
            sys.exit(1)

        trades_deleted = (
            db.query(Trade)
            .filter(Trade.watchlist_entry_id.in_(db.query(WatchlistEntry.id).filter(WatchlistEntry.user_id == user.id)))
            .delete(synchronize_session=False)
        )
        cash_events_deleted = db.query(CashEvent).filter(CashEvent.user_id == user.id).delete()
        db.commit()
        print(f"Deleted {trades_deleted} trades")
        print(f"Deleted {cash_events_deleted} cash events")
        print(f"Watchlist tickers and price history left untouched for '{username}' (and every other user).")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/reset_to_initial_state.py <username>")
        sys.exit(1)
    reset(sys.argv[1])
