"""Manually-run terminal job: reads screener_stocks.txt, fetches history in
batches, evaluates each ticker with the existing core indicator/entry
functions (entry-only, no positions), and truncate+rewrites the
screener_results table in one transaction. The same batch-fetch logic is
also reachable from the screener page's "Refresh" button
(POST /api/screener/refresh) -- both call run_screener_batch(). See
docs/planning/phase-14a-screener-backend.md and
docs/planning/phase-15-screener-refresh.md for the full design.

Usage: python scripts/run_screener.py
"""

from stockmon.db.base import SessionLocal
from stockmon.services.screener_service import read_screener_universe, run_screener_batch, save_screener_run
from stockmon.services.yfinance_provider import YFinanceProvider


def main() -> None:
    tickers = read_screener_universe()
    print(f"Screener run starting: {len(tickers)} tickers")

    provider = YFinanceProvider()
    result = run_screener_batch(provider)

    db = SessionLocal()
    try:
        save_screener_run(db, result.rows, result.run_at)
    finally:
        db.close()

    print(f"Screener run complete: {len(result.rows)} succeeded, {len(result.failures)} failed")
    if result.failures:
        print("Failed: " + ", ".join(f"{f.ticker} ({f.error})" for f in result.failures))


if __name__ == "__main__":
    main()
