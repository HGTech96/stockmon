"""Bulk-import a chronologically ordered CSV of past deposits/withdrawals/
buys/sells into an already-populated DB. Not a migration -- runs on top of
whatever trades/cash events already exist. See docs/planning/phase-10b-csv-
importer.md for the full design.

Usage: python scripts/import_history.py path/to/history.csv
"""

import sys

from stockmon.db.base import SessionLocal
from stockmon.services.import_service import ImportError as ImportValidationError
from stockmon.services.import_service import import_rows, parse_csv_rows


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/import_history.py path/to/history.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    db = SessionLocal()
    try:
        with open(csv_path, newline="") as fileobj:
            rows = parse_csv_rows(fileobj)
        summary = import_rows(db, rows)
        print(f"Imported {summary.trades_added} trades, {summary.cash_events_added} cash events")
    except ImportValidationError as exc:
        print(f"Import failed, nothing written: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
