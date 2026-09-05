from stockmon.services.auth_service import LOGIN_LOCKOUT_MAX_ATTEMPTS, create_user

USER_KEYS = {"id", "username", "email"}


def test_login_success_sets_cookie_and_returns_user(client, db) -> None:
    create_user(db, "alice", "password123", "alice@example.com")

    r = client.post("/api/auth/login", json={"username": "alice", "password": "password123"})

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == USER_KEYS
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "session_id" in r.cookies


def test_login_wrong_password_is_401(client, db) -> None:
    create_user(db, "alice", "password123")

    r = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})

    assert r.status_code == 401
    assert set(r.json().keys()) == {"error"}


def test_login_unknown_username_is_401(client) -> None:
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "password123"})
    assert r.status_code == 401


def test_me_without_session_is_401(client) -> None:
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_me_with_session_returns_current_user(client, db) -> None:
    create_user(db, "alice", "password123")
    client.post("/api/auth/login", json={"username": "alice", "password": "password123"})

    r = client.get("/api/auth/me")

    assert r.status_code == 200
    assert r.json()["username"] == "alice"


def test_logout_clears_session(client, db) -> None:
    create_user(db, "alice", "password123")
    client.post("/api/auth/login", json={"username": "alice", "password": "password123"})

    r = client.post("/api/auth/logout")
    assert r.status_code == 204

    r2 = client.get("/api/auth/me")
    assert r2.status_code == 401


def test_logout_without_session_is_noop(client) -> None:
    r = client.post("/api/auth/logout")
    assert r.status_code == 204


def test_login_locked_out_after_max_failed_attempts_returns_429(client, db) -> None:
    create_user(db, "alice", "password123")
    for _ in range(LOGIN_LOCKOUT_MAX_ATTEMPTS):
        client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})

    r = client.post("/api/auth/login", json={"username": "alice", "password": "password123"})

    assert r.status_code == 429
    assert set(r.json().keys()) == {"error"}
