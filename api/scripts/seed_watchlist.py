"""Add the starter watchlist tickers to one user's watchlist (idempotent).
Tickers (shared market-data rows) are created if they don't already exist;
the watchlist entry linking them to this user is what's actually per-user.

Usage: python scripts/seed_watchlist.py <username>
"""

import sys

from stockmon.db.base import SessionLocal
from stockmon.db.models import Ticker, User, WatchlistEntry

WATCHLIST = {
    "AAPL": "Apple Inc.",
    "NFLX": "Netflix, Inc.",
    "QCOM": "QUALCOMM Incorporated",
    "RKLB": "Rocket Lab USA, Inc.",
    "TSLA": "Tesla, Inc.",
    "AVGO": "Broadcom Inc.",
    "ORCL": "Oracle Corporation",
    "NVDA": "NVIDIA Corporation",
    "AVAV": "AeroVironment, Inc.",
    "CRTO": "Criteo S.A.",
    "AMZN": "Amazon.com, Inc.",
    "MSFT": "Microsoft Corporation",
    "META": "Meta Platforms, Inc.",
}


def seed(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            print(f"No user '{username}' -- run scripts/create_user.py first")
            sys.exit(1)

        tickers_by_symbol = {t.ticker: t for t in db.query(Ticker).all()}
        existing_entry_ticker_ids = {
            e.ticker_id for e in db.query(WatchlistEntry).filter(WatchlistEntry.user_id == user.id).all()
        }

        added = []
        for ticker, company_name in WATCHLIST.items():
            ticker_row = tickers_by_symbol.get(ticker)
            if ticker_row is None:
                ticker_row = Ticker(ticker=ticker, company_name=company_name)
                db.add(ticker_row)
                db.flush()
                tickers_by_symbol[ticker] = ticker_row

            if ticker_row.id in existing_entry_ticker_ids:
                continue
            db.add(WatchlistEntry(user_id=user.id, ticker_id=ticker_row.id))
            added.append(ticker)

        db.commit()
        print(f"Added {len(added)} stocks to {username}'s watchlist: {added}")
        print(f"Skipped {len(existing_entry_ticker_ids)} already present")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_watchlist.py <username>")
        sys.exit(1)
    seed(sys.argv[1])
