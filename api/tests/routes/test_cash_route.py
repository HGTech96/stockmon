from datetime import date, timedelta

from tests.conftest import make_stock

CASH_LIST_KEYS = {"meta", "cashAvailable", "events"}
CASH_EVENT_KEYS = {"id", "type", "amountUsd", "date"}
CASH_EVENT_RESPONSE_KEYS = {"event", "cashAvailable"}


def test_get_cash_empty(client, db) -> None:
    r = client.get("/api/cash")

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == CASH_LIST_KEYS
    assert body["cashAvailable"] == 0.0
    assert body["events"] == []


def test_post_deposit_returns_201(client, db) -> None:
    r = client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"})

    assert r.status_code == 201
    body = r.json()
    assert set(body.keys()) == CASH_EVENT_RESPONSE_KEYS
    assert set(body["event"].keys()) == CASH_EVENT_KEYS
    assert body["event"]["type"] == "deposit"
    assert body["cashAvailable"] == 100.0


def test_get_cash_populated_newest_first(client, db) -> None:
    client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"})
    client.post("/api/cash", json={"type": "withdraw", "amountUsd": 20, "date": "2026-01-05"})

    r = client.get("/api/cash")

    assert r.status_code == 200
    body = r.json()
    assert body["cashAvailable"] == 80.0
    assert [e["type"] for e in body["events"]] == ["withdraw", "deposit"]


def test_post_withdraw_exceeding_cash_returns_422(client, db) -> None:
    client.post("/api/cash", json={"type": "deposit", "amountUsd": 50, "date": "2026-01-01"})

    r = client.post("/api/cash", json={"type": "withdraw", "amountUsd": 100, "date": "2026-01-02"})

    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_post_amount_must_be_positive_returns_422(client, db) -> None:
    r = client.post("/api/cash", json={"type": "deposit", "amountUsd": 0, "date": "2026-01-01"})

    assert r.status_code == 422


def test_post_future_date_returns_422(client, db) -> None:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = client.post("/api/cash", json={"type": "deposit", "amountUsd": 10, "date": tomorrow})

    assert r.status_code == 422


def test_delete_cash_event_returns_204(client, db) -> None:
    created = client.post("/api/cash", json={"type": "deposit", "amountUsd": 100, "date": "2026-01-01"}).json()

    r = client.delete(f"/api/cash/{created['event']['id']}")

    assert r.status_code == 204
    assert client.get("/api/cash").json()["events"] == []


def test_delete_cash_event_not_found_returns_404(client, db) -> None:
    r = client.delete("/api/cash/999")

    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}


def test_delete_deposit_a_later_buy_depends_on_returns_422(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    deposit = client.post("/api/cash", json={"type": "deposit", "amountUsd": 1000, "date": "2026-01-01"}).json()
    client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 10, "pricePerShare": 100, "date": "2026-01-02"},
    )

    r = client.delete(f"/api/cash/{deposit['event']['id']}")

    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_buy_exceeding_cash_returns_422(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    client.post("/api/cash", json={"type": "deposit", "amountUsd": 500, "date": "2026-01-01"})

    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 10, "pricePerShare": 100, "date": "2026-01-02"},
    )

    assert r.status_code == 422
    assert r.json()["error"] == "Insufficient cash — record a deposit first."
