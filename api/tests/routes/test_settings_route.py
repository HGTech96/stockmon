from tests.conftest import make_stock

SETTINGS_KEYS = {"defaultProfitTargetDollars", "perPositionTargets"}


def test_get_settings_returns_default(authed_client) -> None:
    r = authed_client.get("/api/settings")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == SETTINGS_KEYS
    assert body["defaultProfitTargetDollars"] == 50.0
    assert body["perPositionTargets"] == {}


def test_put_settings_updates_default(authed_client) -> None:
    r = authed_client.put("/api/settings", json={"defaultProfitTargetDollars": 75.0})
    assert r.status_code == 200
    assert r.json()["defaultProfitTargetDollars"] == 75.0

    r2 = authed_client.get("/api/settings")
    assert r2.json()["defaultProfitTargetDollars"] == 75.0


def test_put_position_target(authed_client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    r = authed_client.put("/api/settings/targets/AAPL", json={"targetDollars": 150.0})
    assert r.status_code == 200
    assert r.json()["perPositionTargets"] == {"AAPL": 150.0}


def test_put_position_target_unknown_ticker_is_404(authed_client) -> None:
    r = authed_client.put("/api/settings/targets/ZZZZ", json={"targetDollars": 150.0})
    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}


def test_delete_position_target_clears_override(authed_client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    authed_client.put("/api/settings/targets/AAPL", json={"targetDollars": 150.0})

    r = authed_client.delete("/api/settings/targets/AAPL")
    assert r.status_code == 204

    r2 = authed_client.get("/api/settings")
    assert r2.json()["perPositionTargets"] == {}


def test_delete_position_target_noop_without_existing_override(authed_client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    r = authed_client.delete("/api/settings/targets/AAPL")
    assert r.status_code == 204


def test_delete_position_target_unknown_ticker_is_404(authed_client) -> None:
    r = authed_client.delete("/api/settings/targets/ZZZZ")
    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}
