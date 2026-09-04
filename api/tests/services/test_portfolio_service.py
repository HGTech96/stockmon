from datetime import date
from decimal import Decimal

from stockmon.db.models import Trade
from stockmon.services.portfolio_service import get_portfolio
from tests.conftest import make_daily_prices, make_stock, make_user


def test_empty_state_no_trades(db) -> None:
    user = make_user(db)
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    make_stock(db, "NVDA", "NVIDIA Corporation", user=user)

    portfolio = get_portfolio(db, user.id)

    assert portfolio.has_trades is False
    assert portfolio.summary is None
    assert portfolio.money is None
    assert portfolio.positions == []
    assert portfolio.watchlist == ["AAPL", "NVDA"]


def test_open_position_appears_with_profit_target(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "NVDA", "NVIDIA Corporation", user=user)
    make_daily_prices(db, stock, ["80.00"] * 29 + ["128.55"])
    db.add(
        Trade(watchlist_entry_id=stock.id, action="buy", shares=Decimal(25), price_per_share=Decimal("88.10"), trade_date=date(2026, 1, 1))
    )
    db.commit()

    portfolio = get_portfolio(db, user.id)

    assert portfolio.has_trades is True
    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.ticker == "NVDA"
    assert position.position.shares_held == Decimal(25)
    assert portfolio.summary is not None
    assert portfolio.summary.total_invested == Decimal("2202.50")
    assert portfolio.money is not None


def test_closed_position_excluded_from_positions_list(db) -> None:
    user = make_user(db)
    stock = make_stock(db, "AAPL", "Apple Inc.", user=user)
    make_daily_prices(db, stock, ["100.00"] * 30)
    db.add_all(
        [
            Trade(watchlist_entry_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1)),
            Trade(watchlist_entry_id=stock.id, action="sell", shares=Decimal(10), price_per_share=Decimal(110), trade_date=date(2026, 1, 5)),
        ]
    )
    db.commit()

    portfolio = get_portfolio(db, user.id)

    assert portfolio.has_trades is True
    assert portfolio.positions == []
    assert portfolio.summary is None
    assert portfolio.money is not None  # trades exist even though summary is null


def test_watchlist_present_even_with_no_stocks(db) -> None:
    user = make_user(db)
    portfolio = get_portfolio(db, user.id)
    assert portfolio.watchlist == []
    assert portfolio.has_trades is False


def test_portfolio_only_shows_this_users_watchlist(db) -> None:
    user = make_user(db, username="user")
    other = make_user(db, username="other")
    make_stock(db, "AAPL", "Apple Inc.", user=user)
    make_stock(db, "MSFT", "Microsoft Corporation", user=other)

    portfolio = get_portfolio(db, user.id)

    assert portfolio.watchlist == ["AAPL"]
