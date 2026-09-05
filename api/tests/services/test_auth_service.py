from datetime import datetime, timedelta, timezone

import pytest

from stockmon.db.models import LoginAttempt
from stockmon.services.auth_service import (
    LOGIN_LOCKOUT_MAX_ATTEMPTS,
    InvalidCredentialsError,
    TooManyAttemptsError,
    UsernameTakenError,
    authenticate,
    clear_login_lockout,
    create_session,
    create_user,
    delete_session,
    get_user_by_session,
    hash_password,
    verify_password,
)


def test_hash_password_round_trips() -> None:
    hashed = hash_password("correct-horse")
    assert verify_password("correct-horse", hashed)
    assert not verify_password("wrong-password", hashed)


def test_hash_password_uses_a_random_salt_per_call() -> None:
    assert hash_password("same-password") != hash_password("same-password")


def test_create_user(db) -> None:
    user = create_user(db, "alice", "password123", "alice@example.com")
    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert verify_password("password123", user.password_hash)


def test_create_user_without_email(db) -> None:
    user = create_user(db, "bob", "password123")
    assert user.email is None


def test_create_user_duplicate_username_raises(db) -> None:
    create_user(db, "alice", "password123")
    with pytest.raises(UsernameTakenError):
        create_user(db, "alice", "different-password")


def test_authenticate_success(db) -> None:
    create_user(db, "alice", "password123")
    user = authenticate(db, "alice", "password123")
    assert user.username == "alice"


def test_authenticate_wrong_password_raises(db) -> None:
    create_user(db, "alice", "password123")
    with pytest.raises(InvalidCredentialsError):
        authenticate(db, "alice", "wrong-password")


def test_authenticate_unknown_username_raises(db) -> None:
    with pytest.raises(InvalidCredentialsError):
        authenticate(db, "nobody", "password123")


def test_create_session_and_look_up_by_id(db) -> None:
    user = create_user(db, "alice", "password123")
    session = create_session(db, user.id)

    found = get_user_by_session(db, session.id)

    assert found is not None
    assert found.id == user.id


def test_get_user_by_session_unknown_id_returns_none(db) -> None:
    assert get_user_by_session(db, "does-not-exist") is None


def test_get_user_by_session_expired_returns_none_and_deletes_row(db) -> None:
    from stockmon.db.models import UserSession

    user = create_user(db, "alice", "password123")
    expired = UserSession(
        id="expired-session",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db.add(expired)
    db.commit()

    assert get_user_by_session(db, "expired-session") is None
    assert db.get(UserSession, "expired-session") is None


def test_delete_session_revokes_it(db) -> None:
    user = create_user(db, "alice", "password123")
    session = create_session(db, user.id)

    delete_session(db, session.id)

    assert get_user_by_session(db, session.id) is None


def test_delete_session_unknown_id_is_noop(db) -> None:
    delete_session(db, "does-not-exist")


def test_lockout_after_max_failed_attempts(db) -> None:
    create_user(db, "alice", "password123")
    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(InvalidCredentialsError):
            authenticate(db, "alice", "wrong-password")

    with pytest.raises(TooManyAttemptsError):
        authenticate(db, "alice", "password123")  # correct password, still locked


def test_lockout_applies_to_unknown_usernames_too(db) -> None:
    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(InvalidCredentialsError):
            authenticate(db, "nobody", "whatever")

    with pytest.raises(TooManyAttemptsError):
        authenticate(db, "nobody", "whatever")


def test_lockout_ignores_attempts_outside_the_window(db) -> None:
    create_user(db, "alice", "password123")
    old = datetime.now(timezone.utc) - timedelta(minutes=20)
    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        db.add(LoginAttempt(username="alice", attempted_at=old, succeeded=False))
    db.commit()

    # All failures are outside the 15-minute window -- not locked out.
    user = authenticate(db, "alice", "password123")
    assert user.username == "alice"


def test_lockout_does_not_affect_other_usernames(db) -> None:
    create_user(db, "alice", "password123")
    create_user(db, "bob", "password456")
    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(InvalidCredentialsError):
            authenticate(db, "alice", "wrong-password")

    user = authenticate(db, "bob", "password456")
    assert user.username == "bob"


def test_clear_login_lockout_allows_login_again(db) -> None:
    create_user(db, "alice", "password123")
    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        with pytest.raises(InvalidCredentialsError):
            authenticate(db, "alice", "wrong-password")

    deleted = clear_login_lockout(db, "alice")

    assert deleted == LOGIN_LOCKOUT_MAX_ATTEMPTS
    user = authenticate(db, "alice", "password123")
    assert user.username == "alice"
