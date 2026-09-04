"""Bulk-import a chronologically ordered CSV of past deposits/withdrawals/
buys/sells into an already-populated DB, for one user. Not a migration --
runs on top of whatever trades/cash events already exist. See
docs/planning/phase-10b-csv-importer.md for the full design.

Usage: python scripts/import_history.py <username> path/to/history.csv
"""

import sys

from stockmon.db.base import SessionLocal
from stockmon.db.models import User
from stockmon.services.import_service import ImportError as ImportValidationError
from stockmon.services.import_service import import_rows, parse_csv_rows


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python scripts/import_history.py <username> path/to/history.csv")
        sys.exit(1)

    username, csv_path = sys.argv[1], sys.argv[2]
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            print(f"No user '{username}' -- run scripts/create_user.py first")
            sys.exit(1)

        with open(csv_path, newline="") as fileobj:
            rows = parse_csv_rows(fileobj)
        summary = import_rows(db, user.id, rows)
        print(f"Imported {summary.trades_added} trades, {summary.cash_events_added} cash events")
    except ImportValidationError as exc:
        print(f"Import failed, nothing written: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
