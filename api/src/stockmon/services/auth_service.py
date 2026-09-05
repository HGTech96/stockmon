import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from stockmon.db.models import LoginAttempt
from stockmon.db.models import User as UserRow
from stockmon.db.models import UserSession as SessionRow

# Fixed lifetime from creation -- no sliding renewal (see
# docs/planning/phase-23-multi-user-accounts.md).
SESSION_LIFETIME = timedelta(days=30)

_PBKDF2_ALGORITHM = "sha256"
_PBKDF2_ITERATIONS = 600_000

# Sliding-window lockout (see docs/planning/phase-24-deployment.md): no
# separate "locked until" state -- a username is locked whenever it has
# this many failed attempts within this window, so a lock self-clears as
# old failures age out rather than needing its own expiry bookkeeping.
LOGIN_LOCKOUT_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_WINDOW = timedelta(minutes=15)


class UsernameTakenError(Exception):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Username '{username}' is already taken")


class InvalidCredentialsError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid username or password")


class TooManyAttemptsError(Exception):
    def __init__(self) -> None:
        super().__init__("Too many failed login attempts. Try again in a few minutes.")


def hash_password(password: str) -> str:
    """stdlib PBKDF2-HMAC-SHA256 with a random per-user salt -- no
    third-party dependency needed for a small, admin-created user base."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(_PBKDF2_ALGORITHM, password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, _, digest_hex = password_hash.partition("$")
    if not digest_hex:
        return False
    candidate = hashlib.pbkdf2_hmac(_PBKDF2_ALGORITHM, password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return secrets.compare_digest(candidate.hex(), digest_hex)


def create_user(db: Session, username: str, password: str, email: str | None = None) -> UserRow:
    if db.query(UserRow).filter(UserRow.username == username).first() is not None:
        raise UsernameTakenError(username)
    user = UserRow(username=username, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _is_locked_out(db: Session, username: str) -> bool:
    window_start = datetime.now(timezone.utc) - LOGIN_LOCKOUT_WINDOW
    failed_count = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.username == username,
            LoginAttempt.succeeded.is_(False),
            LoginAttempt.attempted_at >= window_start,
        )
        .count()
    )
    return failed_count >= LOGIN_LOCKOUT_MAX_ATTEMPTS


def _record_login_attempt(db: Session, username: str, succeeded: bool) -> None:
    db.add(LoginAttempt(username=username, succeeded=succeeded))
    db.commit()


def authenticate(db: Session, username: str, password: str) -> UserRow:
    """Checks the sliding-window lockout BEFORE touching the password --
    a locked-out username is rejected the same way regardless of whether
    the password would've been right, so lockout state itself doesn't leak
    anything about which usernames are real (same as the ordinary
    "unknown username or wrong password" case below, which also doesn't
    distinguish the two)."""
    if _is_locked_out(db, username):
        raise TooManyAttemptsError()

    user = db.query(UserRow).filter(UserRow.username == username).first()
    succeeded = user is not None and verify_password(password, user.password_hash)
    _record_login_attempt(db, username, succeeded)

    if not succeeded:
        raise InvalidCredentialsError()
    assert user is not None
    return user


def clear_login_lockout(db: Session, username: str) -> int:
    """Deletes every recorded attempt for a username (not just the failed
    ones) -- the simplest possible manual reset, used by
    scripts/reset_login_lockout.py. Returns the number of rows removed."""
    deleted = db.query(LoginAttempt).filter(LoginAttempt.username == username).delete()
    db.commit()
    return deleted


def create_session(db: Session, user_id: int) -> SessionRow:
    now = datetime.now(timezone.utc)
    session = SessionRow(
        id=secrets.token_urlsafe(32),
        user_id=user_id,
        created_at=now,
        expires_at=now + SESSION_LIFETIME,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_by_session(db: Session, session_id: str) -> UserRow | None:
    session = db.get(SessionRow, session_id)
    if session is None:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    return db.get(UserRow, session.user_id)


def delete_session(db: Session, session_id: str) -> None:
    session = db.get(SessionRow, session_id)
    if session is not None:
        db.delete(session)
        db.commit()
