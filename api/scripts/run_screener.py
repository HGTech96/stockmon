"""Manually-run terminal job: reads screener_stocks.txt, fetches history in
batches, evaluates each ticker with the existing core indicator/entry
functions (entry-only, no positions), and truncate+rewrites the
screener_results table in one transaction. See
docs/planning/phase-14a-screener-backend.md for the full design.

Usage: python scripts/run_screener.py
"""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from stockmon.db.base import SessionLocal
from stockmon.services.screener_service import (
    ScreenerFetchFailure,
    ScreenerRow,
    fetch_and_evaluate_ticker,
    read_screener_universe,
    save_screener_run,
)
from stockmon.services.yfinance_provider import YFinanceProvider

BATCH_SIZE = 10
BATCH_PAUSE_SECONDS = 1.5


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main() -> None:
    tickers = read_screener_universe()
    print(f"Screener run starting: {len(tickers)} tickers, batch size {BATCH_SIZE}")

    provider = YFinanceProvider()
    rows: list[ScreenerRow] = []
    failures: list[ScreenerFetchFailure] = []
    batches = _chunks(tickers, BATCH_SIZE)

    for i, batch in enumerate(batches):
        with ThreadPoolExecutor(max_workers=len(batch)) as pool:
            for result in pool.map(lambda ticker: fetch_and_evaluate_ticker(provider, ticker), batch):
                if isinstance(result, ScreenerRow):
                    rows.append(result)
                else:
                    failures.append(result)

        done = len(rows) + len(failures)
        print(f"[{done}/{len(tickers)}] done")
        if i < len(batches) - 1:
            time.sleep(BATCH_PAUSE_SECONDS)

    db = SessionLocal()
    try:
        run_at = datetime.now().astimezone()
        save_screener_run(db, rows, run_at)
    finally:
        db.close()

    print(f"Screener run complete: {len(rows)} succeeded, {len(failures)} failed")
    if failures:
        print("Failed: " + ", ".join(f"{f.ticker} ({f.error})" for f in failures))


if __name__ == "__main__":
    main()
