"""Insert the watchlist tickers into the stocks table (idempotent)."""

from stockmon.db.base import SessionLocal
from stockmon.db.models import Stock

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


def seed() -> None:
    db = SessionLocal()
    try:
        existing = {ticker for (ticker,) in db.query(Stock.ticker).all()}
        added = []
        for ticker, company_name in WATCHLIST.items():
            if ticker in existing:
                continue
            db.add(Stock(ticker=ticker, company_name=company_name))
            added.append(ticker)
        db.commit()
        print(f"Added {len(added)} stocks: {added}")
        print(f"Skipped {len(existing)} already present")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
