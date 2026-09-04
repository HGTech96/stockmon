from datetime import datetime, timedelta, timezone

import pytest

from stockmon.services.auth_service import (
    InvalidCredentialsError,
    UsernameTakenError,
    authenticate,
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
