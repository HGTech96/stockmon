from datetime import date
from decimal import Decimal

from stockmon.core.position import TradeEvent, derive_position
from stockmon.db.models import Trade
from stockmon.services.stock_service import evaluate_stock_snapshot
from tests.conftest import make_daily_prices, make_stock

TARGET = Decimal("50.00")


def test_ok_status_with_thirty_bars_and_no_position(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["90.00"])

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "ok"
    assert evaluation.indicators is not None
    assert evaluation.current_price == Decimal("90.00")
    assert evaluation.position is None
    assert evaluation.position_value is None
    assert evaluation.suggestion is not None
    assert evaluation.suggestion.type == "entry"


def test_insufficient_history_falls_back_to_price_snapshot(db) -> None:
    stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.")
    make_daily_prices(db, stock, ["12.00", "13.42"])

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "insufficient_history"
    assert evaluation.indicators is None
    assert evaluation.suggestion is None
    assert evaluation.warning is None
    assert evaluation.current_price == Decimal("13.42")
    assert evaluation.days_available == 2


def test_never_refreshed_has_no_current_price(db) -> None:
    stock = make_stock(db, "NEW", "Newly Added Inc.")

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "insufficient_history"
    assert evaluation.current_price is None
    assert evaluation.days_available == 0


def test_owned_stock_computes_position_value_when_ok(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["120.00"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)))
    db.commit()

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.position is not None
    assert evaluation.position_value is not None
    assert evaluation.position_value.profit_loss == Decimal(200)
    assert evaluation.suggestion is not None


def test_owned_stock_insufficient_history_still_has_position_value(db) -> None:
    stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.")
    make_daily_prices(db, stock, ["12.00", "13.00"])
    db.add(Trade(stock_id=stock.id, action="buy", shares=Decimal(5), price_per_share=Decimal(10), trade_date=date(2026, 1, 1)))
    db.commit()

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    assert evaluation.status == "insufficient_history"
    assert evaluation.position is not None
    assert evaluation.position_value is not None
    assert evaluation.position_value.current_value == Decimal(65)
    assert evaluation.suggestion is None


def test_trade_events_loaded_in_chronological_order(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 30)
    db.add_all(
        [
            Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 5)),
            Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(120), trade_date=date(2026, 1, 1)),
        ]
    )
    db.commit()

    evaluation = evaluate_stock_snapshot(db, stock, TARGET)

    expected = derive_position(
        [
            TradeEvent(action="buy", shares=Decimal(10), price_per_share=Decimal(120), date=date(2026, 1, 1)),
            TradeEvent(action="buy", shares=Decimal(10), price_per_share=Decimal(100), date=date(2026, 1, 5)),
        ]
    )
    assert evaluation.position == expected
