from datetime import date, timedelta

from tests.conftest import make_stock

CASH_LIST_KEYS = {"meta", "cashAvailable", "events"}
CASH_EVENT_KEYS = {"id", "type", "amountUsd", "date"}
CASH_EVENT_RESPONSE_KEYS = {"event", "cashAvailable"}


def test_get_cash_empty(authed_client, db) -> None:
    r = authed_client.get("/api/cash")

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == CASH_LIST_KEYS
    assert body["cashAvailable"] == 0.0
    assert body["events"] == []


def test_post_deposit_returns_201(authed_client, db) -> None:
    r = authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"})

    assert r.status_code == 201
    body = r.json()
    assert set(body.keys()) == CASH_EVENT_RESPONSE_KEYS
    assert set(body["event"].keys()) == CASH_EVENT_KEYS
    assert body["event"]["type"] == "deposit"
    assert body["cashAvailable"] == 100.0


def test_get_cash_populated_newest_first(authed_client, db) -> None:
    authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"})
    authed_client.post("/api/cash", json={"type": "withdraw", "amountUsd": 20, "date": "2026-01-05"})

    r = authed_client.get("/api/cash")

    assert r.status_code == 200
    body = r.json()
    assert body["cashAvailable"] == 80.0
    assert [e["type"] for e in body["events"]] == ["withdraw", "deposit"]


def test_post_withdraw_exceeding_cash_returns_422(authed_client, db) -> None:
    authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 50, "date": "2026-01-01"})

    r = authed_client.post("/api/cash", json={"type": "withdraw", "amountUsd": 100, "date": "2026-01-02"})

    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_post_amount_must_be_positive_returns_422(authed_client, db) -> None:
    r = authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 0, "date": "2026-01-01"})

    assert r.status_code == 422


def test_post_future_date_returns_422(authed_client, db) -> None:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 10, "date": tomorrow})

    assert r.status_code == 422


def test_delete_cash_event_returns_204(authed_client, db) -> None:
    created = authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"}).json()

    r = authed_client.delete(f"/api/cash/{created['event']['id']}")

    assert r.status_code == 204
    assert authed_client.get("/api/cash").json()["events"] == []


def test_delete_cash_event_not_found_returns_404(authed_client, db) -> None:
    r = authed_client.delete("/api/cash/999")

    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}


def test_delete_deposit_a_later_buy_depends_on_returns_422(authed_client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    deposit = authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 1000, "date": "2026-01-01"}).json()
    authed_client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 10, "pricePerShare": 100, "date": "2026-01-02"},
    )

    r = authed_client.delete(f"/api/cash/{deposit['event']['id']}")

    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_buy_exceeding_cash_returns_422(authed_client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    authed_client.post("/api/cash", json={"type": "deposit", "amountUsd": 500, "date": "2026-01-01"})

    r = authed_client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 10, "pricePerShare": 100, "date": "2026-01-02"},
    )

    assert r.status_code == 422
    assert r.json()["error"] == "Insufficient cash — record a deposit first."
