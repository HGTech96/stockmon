from datetime import date
from decimal import Decimal

from stockmon.db.models import Trade
from stockmon.services.dashboard_service import build_dashboard
from tests.conftest import make_daily_prices, make_stock, make_user


def test_no_stocks_has_empty_list_and_no_summary(db) -> None:
    user = make_user(db)
    dashboard = build_dashboard(db, user.id)
    assert dashboard.stocks == []
    assert dashboard.summary is None
    assert dashboard.money is None


def test_no_trades_has_null_summary(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "AAPL", "Apple Inc.", user=user)
    make_daily_prices(db, stock, ["100.00"] * 30)

    dashboard = build_dashboard(db, user.id)

    assert dashboard.summary is None
    assert len(dashboard.stocks) == 1
    assert dashboard.stocks[0].position is None


def test_summary_aggregates_owned_positions(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "AAPL", "Apple Inc.", user=user)
    make_daily_prices(db, stock, ["100.00"] * 29 + ["120.00"])
    db.add(
        Trade(watchlist_entry_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    )
    db.commit()

    dashboard = build_dashboard(db, user.id)

    assert dashboard.summary is not None
    assert dashboard.summary.total_invested == Decimal(1000)
    assert dashboard.summary.total_current_value == Decimal(1200)
    assert dashboard.summary.total_profit_loss == Decimal(200)
    assert dashboard.summary.total_profit_loss_pct == Decimal(20)
    assert dashboard.money is not None
    assert dashboard.money.unrealized_gain_open == Decimal(200)


def test_dashboard_rows_are_sorted(db) -> None:
    user = make_user(db)
    sell_stock = make_stock(db, "TSLA", "Tesla, Inc.", user=user)
    make_daily_prices(db, sell_stock, ["100.00"] * 29 + ["70.00"])  # sharp drop -> warning, no position -> WAIT
    buy_stock = make_stock(db, "AAPL", "Apple Inc.", user=user)
    # rigged to be a clear BUY: below avg, near low, low RSI, high volume
    closes = ["120.00"] * 20 + [str(120 - i) for i in range(1, 11)]
    make_daily_prices(db, buy_stock, closes, volumes=[1000] * 29 + [5_000_000])
    insufficient_stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.", user=user)
    make_daily_prices(db, insufficient_stock, ["13.00", "13.42"])

    dashboard = build_dashboard(db, user.id)
    tickers = [row.ticker for row in dashboard.stocks]

    # insufficient-history always sorts last regardless of the others' order
    assert tickers[-1] == "RIVN"
    assert set(tickers) == {"TSLA", "AAPL", "RIVN"}


def test_dashboard_only_shows_this_users_stocks(db) -> None:
    user = make_user(db, username="user")
    other = make_user(db, username="other")
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    make_stock(db, "MSFT", "Microsoft Corporation", user=other)

    dashboard = build_dashboard(db, user.id)

    assert [row.ticker for row in dashboard.stocks] == ["AAPL"]
