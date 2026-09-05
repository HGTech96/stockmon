"""Manually-run terminal script to clear a username's login lockout --
there is no self-service unlock (see
docs/planning/phase-24-deployment.md's sliding-window lockout: 5 failed
attempts within 15 minutes locks a username out, and it normally
self-clears as those attempts age out on their own). This just deletes
that username's recorded attempts outright, for when waiting isn't
convenient.

Usage: python scripts/reset_login_lockout.py <username>
"""

import sys

from stockmon.db.base import SessionLocal
from stockmon.services.auth_service import clear_login_lockout


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/reset_login_lockout.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    db = SessionLocal()
    try:
        deleted = clear_login_lockout(db, username)
    finally:
        db.close()

    print(f"Cleared {deleted} login attempt(s) for '{username}'")


if __name__ == "__main__":
    main()
