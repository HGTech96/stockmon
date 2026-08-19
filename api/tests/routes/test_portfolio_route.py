from datetime import date
from decimal import Decimal

from stockmon.db.models import Trade
from tests.conftest import make_daily_prices, make_stock

PORTFOLIO_TOP_KEYS = {"meta", "hasTrades", "summary", "positions", "watchlist"}
POSITION_KEYS = {
    "ticker", "companyName", "sharesHeld", "avgPurchasePrice", "amountInvested", "currentValue",
    "profitLoss", "profitLossPct", "profitTarget", "status", "suggestion",
}


def test_empty_state(client, db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    make_stock(db, "NVDA", "NVIDIA Corporation")

    r = client.get("/api/portfolio")
    assert r.status_code == 200
    body = r.json()

    assert set(body.keys()) == PORTFOLIO_TOP_KEYS
    assert body["hasTrades"] is False
    assert body["summary"] is None
    assert body["positions"] == []
    assert body["watchlist"] == ["AAPL", "NVDA"]


def test_open_position_shape(client, db) -> None:
    stock = make_stock(db, "NVDA", "NVIDIA Corporation")
    make_daily_prices(db, stock, ["80.00"] * 29 + ["128.55"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(25), price_per_share=Decimal("88.10"), trade_date=date(2026, 1, 1)))
    db.commit()

    body = client.get("/api/portfolio").json()

    assert body["hasTrades"] is True
    assert len(body["positions"]) == 1
    position = body["positions"][0]
    assert set(position.keys()) == POSITION_KEYS
    assert position["ticker"] == "NVDA"
    assert position["sharesHeld"] == 25.0
    assert position["amountInvested"] == 2202.5


def test_closed_position_excluded(client, db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 30)
    db.add_all(
        [
            Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)),
            Trade(stock_id=stock.id, action="sell", shares=Decimal(10), price_per_share=Decimal(110), trade_date=date(2026, 1, 5)),
        ]
    )
    db.commit()

    body = client.get("/api/portfolio").json()
    assert body["hasTrades"] is True
    assert body["positions"] == []
