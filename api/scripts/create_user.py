"""Manually-run terminal script to create a user account -- there is no
self-service signup endpoint by design (see
docs/planning/phase-23-multi-user-accounts.md). Prompts for username,
optional email, and password (hidden input, confirmed).

Usage: python scripts/create_user.py
"""

import getpass

from stockmon.db.base import SessionLocal
from stockmon.services.auth_service import UsernameTakenError, create_user


def main() -> None:
    username = input("Username: ").strip()
    email = input("Email (optional, press enter to skip): ").strip() or None
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords don't match.")
        return

    db = SessionLocal()
    try:
        user = create_user(db, username, password, email)
    except UsernameTakenError as exc:
        print(str(exc))
        return
    finally:
        db.close()

    print(f"Created user '{user.username}' (id={user.id})")


if __name__ == "__main__":
    main()


