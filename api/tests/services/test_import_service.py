import io
from datetime import date
from decimal import Decimal

import pytest

from stockmon.core.position import TradeEvent, derive_position
from stockmon.db.models import CashEvent, Trade
from stockmon.services.cash_service import record_cash_event
from stockmon.services.import_service import ImportError as ImportValidationError
from stockmon.services.import_service import import_rows, parse_csv_rows
from stockmon.services.trade_service import record_trade
from tests.conftest import make_stock

HEADER = "date,type,ticker,shares,price,amount"


def _import(db, csv_text: str):
    rows = parse_csv_rows(io.StringIO(csv_text))
    return import_rows(db, rows)


def _position(db, stock) -> object:
    rows = db.query(Trade).filter(Trade.stock_id == stock.id).order_by(Trade.trade_date, Trade.id).all()
    events = [TradeEvent(action=r.action, shares=r.shares, price_per_share=r.price_per_share, date=r.trade_date) for r in rows]
    return derive_position(events)


def test_valid_mixed_sequence_imports_cleanly(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-01,deposit,,,,1000.00",
            "2026-01-02,buy,AAPL,5,100.00,",
            "2026-01-10,sell,AAPL,2,150.00,",
            "2026-01-11,withdraw,,,,50.00",
            "2026-01-12,buy,AAPL,1,120.00,",
        ]
    )

    summary = _import(db, csv_text)

    assert summary.trades_added == 3
    assert summary.cash_events_added == 2
    assert db.query(Trade).count() == 3
    assert db.query(CashEvent).count() == 2

    stock = db.query(Trade).first().stock
    position = _position(db, stock)
    assert position is not None
    assert position.shares_held == Decimal(4)


def test_cash_oversell_aborts_and_names_line(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-01,deposit,,,,100.00",
            "2026-01-02,buy,AAPL,10,100.00,",  # needs 1000, only 100 available -> line 3
        ]
    )

    with pytest.raises(ImportValidationError, match="line 3"):
        _import(db, csv_text)

    assert db.query(Trade).count() == 0
    assert db.query(CashEvent).count() == 0


def test_share_oversell_aborts_and_names_line(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-01,deposit,,,,1000.00",
            "2026-01-02,buy,AAPL,5,100.00,",
            "2026-01-10,sell,AAPL,10,150.00,",  # only 5 held -> line 4
        ]
    )

    with pytest.raises(ImportValidationError, match="line 4"):
        _import(db, csv_text)

    assert db.query(Trade).count() == 0
    assert db.query(CashEvent).count() == 0


def test_duplicate_of_existing_db_row_aborts(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    record_cash_event(db, "deposit", Decimal("1000.00"), date(2026, 1, 1))
    record_trade(db, "AAPL", "buy", Decimal(5), Decimal("100.00"), date(2026, 1, 2))

    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-02,buy,AAPL,5,100.00,",  # exact duplicate of the existing trade -> line 2
        ]
    )

    with pytest.raises(ImportValidationError, match="line 2: duplicate of an existing record"):
        _import(db, csv_text)

    assert db.query(Trade).count() == 1
    assert db.query(CashEvent).count() == 1


def test_duplicate_within_csv_aborts(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-01,deposit,,,,1000.00",
            "2026-01-02,buy,AAPL,5,100.00,",
            "2026-01-02,buy,AAPL,5,100.00,",  # exact duplicate of the previous CSV row -> line 4
        ]
    )

    with pytest.raises(ImportValidationError, match="line 4: duplicate of an earlier row in this CSV"):
        _import(db, csv_text)

    assert db.query(Trade).count() == 0
    assert db.query(CashEvent).count() == 0


def test_fractional_buy_imports_with_exact_decimal_shares(db) -> None:
    make_stock(db, "AAPL", "Apple Inc.")
    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-01,deposit,,,,1000.00",
            "2026-01-02,buy,AAPL,1.256789,150.25,",
        ]
    )

    summary = _import(db, csv_text)

    assert summary.trades_added == 1
    trade = db.query(Trade).filter(Trade.action == "buy").first()
    assert trade.shares == Decimal("1.256789")


def test_import_on_top_of_existing_db_continues_replay(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    record_cash_event(db, "deposit", Decimal("1000.00"), date(2026, 1, 1))
    record_trade(db, "AAPL", "buy", Decimal(5), Decimal("100.00"), date(2026, 1, 2))

    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-10,sell,AAPL,3,150.00,",  # only valid if the existing 5 shares are seen
        ]
    )

    summary = _import(db, csv_text)

    assert summary.trades_added == 1
    position = _position(db, stock)
    assert position is not None
    assert position.shares_held == Decimal(2)


def test_unknown_ticker_aborts_and_names_line(db) -> None:
    csv_text = "\n".join(
        [
            HEADER,
            "2026-01-01,deposit,,,,1000.00",
            "2026-01-02,buy,ZZZZ,5,100.00,",
        ]
    )

    with pytest.raises(ImportValidationError, match="line 3: 'ZZZZ' is not on the watchlist"):
        _import(db, csv_text)

    assert db.query(Trade).count() == 0
    assert db.query(CashEvent).count() == 0
