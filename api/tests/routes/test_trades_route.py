from datetime import date, timedelta
from decimal import Decimal

from stockmon.db.models import Trade
from tests.conftest import make_stock

TRADE_RESPONSE_KEYS = {"trade", "updatedPosition"}
TRADE_ITEM_KEYS = {"id", "ticker", "action", "shares", "pricePerShare", "date"}
UPDATED_POSITION_KEYS = {"ticker", "sharesHeld", "avgPurchasePrice", "amountInvested"}


def test_buy_opens_position(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 5, "pricePerShare": 189.10, "date": "2026-01-01"},
    )
    assert r.status_code == 201
    body = r.json()
    assert set(body.keys()) == TRADE_RESPONSE_KEYS
    assert set(body["trade"].keys()) == TRADE_ITEM_KEYS
    assert body["trade"]["ticker"] == "AAPL"
    assert body["trade"]["action"] == "buy"
    assert set(body["updatedPosition"].keys()) == UPDATED_POSITION_KEYS
    assert body["updatedPosition"]["sharesHeld"] == 5.0


def test_sell_that_closes_position_returns_null(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)))
    db.commit()

    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "sell", "shares": 10, "pricePerShare": 150, "date": "2026-01-10"},
    )
    assert r.status_code == 201
    assert r.json()["updatedPosition"] is None


def test_unknown_ticker_returns_422_with_error_shape(client) -> None:
    r = client.post(
        "/api/trades",
        json={"ticker": "ZZZZ", "action": "buy", "shares": 1, "pricePerShare": 10, "date": "2026-01-01"},
    )
    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_negative_shares_returns_422(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": -1, "pricePerShare": 10, "date": "2026-01-01"},
    )
    assert r.status_code == 422
    assert "error" in r.json()


def test_zero_price_returns_422(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 1, "pricePerShare": 0, "date": "2026-01-01"},
    )
    assert r.status_code == 422


def test_oversell_returns_422(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(5), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)))
    db.commit()

    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "sell", "shares": 10, "pricePerShare": 150, "date": "2026-01-10"},
    )
    assert r.status_code == 422


def test_sell_with_no_position_returns_422(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "sell", "shares": 1, "pricePerShare": 10, "date": "2026-01-01"},
    )
    assert r.status_code == 422


def test_future_date_returns_422(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 1, "pricePerShare": 10, "date": tomorrow},
    )
    assert r.status_code == 422


def test_missing_field_returns_422_with_error_shape(client) -> None:
    r = client.post("/api/trades", json={"ticker": "AAPL", "action": "buy", "shares": 1})
    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


TRADE_HISTORY_RESPONSE_KEYS = {"meta", "trades"}
TRADE_HISTORY_ITEM_KEYS = {
    "id",
    "ticker",
    "companyName",
    "action",
    "shares",
    "pricePerShare",
    "totalUsd",
    "realizedPnlUsd",
    "date",
}


def test_get_trades_empty(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")

    r = client.get("/api/trades")

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == TRADE_HISTORY_RESPONSE_KEYS
    assert body["trades"] == []


def test_get_trades_returns_history_newest_first(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "buy", "shares": 10, "pricePerShare": 100, "date": "2026-01-01"},
    )
    client.post(
        "/api/trades",
        json={"ticker": "AAPL", "action": "sell", "shares": 4, "pricePerShare": 150, "date": "2026-01-10"},
    )

    r = client.get("/api/trades")

    assert r.status_code == 200
    trades = r.json()["trades"]
    assert len(trades) == 2
    assert set(trades[0].keys()) == TRADE_HISTORY_ITEM_KEYS
    assert trades[0]["action"] == "sell"
    assert trades[0]["realizedPnlUsd"] == 200.0
    assert trades[0]["totalUsd"] == 600.0
    assert trades[1]["action"] == "buy"
    assert trades[1]["realizedPnlUsd"] is None


def test_put_trade_updates_and_returns_recalculated_position(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    trade = Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    db.add(trade)
    db.commit()
    db.refresh(trade)

    r = client.put(f"/api/trades/{trade.id}", json={"shares": 20, "pricePerShare": 100, "date": "2026-01-01"})

    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == TRADE_RESPONSE_KEYS
    assert set(body["trade"].keys()) == TRADE_ITEM_KEYS
    assert body["trade"]["shares"] == 20.0
    assert body["trade"]["ticker"] == "AAPL"
    assert body["updatedPosition"]["sharesHeld"] == 20.0


def test_put_trade_oversell_returns_422(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    buy = Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    db.add(buy)
    db.commit()
    db.refresh(buy)
    db.add(Trade(stock_id=stock.id, action="sell", shares=Decimal(8), price_per_share=Decimal(150), trade_date=date(2026, 1, 10)))
    db.commit()

    r = client.put(f"/api/trades/{buy.id}", json={"shares": 5, "pricePerShare": 100, "date": "2026-01-01"})

    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_put_trade_invalid_field_returns_422(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    trade = Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    db.add(trade)
    db.commit()
    db.refresh(trade)

    r = client.put(f"/api/trades/{trade.id}", json={"shares": 0, "pricePerShare": 100, "date": "2026-01-01"})

    assert r.status_code == 422


def test_put_trade_not_found_returns_404(client, db) -> None:
    r = client.put("/api/trades/999", json={"shares": 1, "pricePerShare": 10, "date": "2026-01-01"})

    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}


def test_delete_trade_returns_204(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    trade = Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    db.add(trade)
    db.commit()
    db.refresh(trade)

    r = client.delete(f"/api/trades/{trade.id}")

    assert r.status_code == 204
    assert db.query(Trade).filter(Trade.id == trade.id).first() is None


def test_delete_trade_oversell_returns_422(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    first_buy = Trade(stock_id=stock.id, action="buy", shares=Decimal(5), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    second_buy = Trade(stock_id=stock.id, action="buy", shares=Decimal(5), price_per_share=Decimal(100), trade_date=date(2026, 1, 5))
    db.add_all([first_buy, second_buy])
    db.commit()
    db.refresh(second_buy)
    db.add(Trade(stock_id=stock.id, action="sell", shares=Decimal(8), price_per_share=Decimal(150), trade_date=date(2026, 1, 10)))
    db.commit()

    r = client.delete(f"/api/trades/{second_buy.id}")

    assert r.status_code == 422
    assert set(r.json().keys()) == {"error"}


def test_delete_trade_not_found_returns_404(client, db) -> None:
    r = client.delete("/api/trades/999")

    assert r.status_code == 404
    assert set(r.json().keys()) == {"error"}
