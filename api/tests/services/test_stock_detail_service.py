from datetime import date
from decimal import Decimal

import pytest

from stockmon.core.indicators import MIN_HISTORY_DAYS
from stockmon.db.models import Trade
from stockmon.services.settings_service import set_position_target
from stockmon.services.stock_detail_service import get_stock_detail
from stockmon.services.stock_service import StockNotFoundError, set_analysis
from tests.conftest import make_daily_prices, make_stock


def test_unknown_ticker_raises_not_found(db) -> None:
    with pytest.raises(StockNotFoundError):
        get_stock_detail(db, "ZZZZ")


def test_ok_status_has_chart_and_indicators_no_position(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.", investor_relations_url="https://investor.apple.com")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["90.00"])

    detail = get_stock_detail(db, "AAPL")

    assert detail.evaluation.status == "ok"
    assert detail.chart_days is not None
    assert len(detail.chart_days) == 30
    assert detail.thirty_day_average is not None
    assert detail.trading_days_until_ready is None
    assert detail.days_required == MIN_HISTORY_DAYS
    assert detail.user_avg_purchase_price is None
    assert detail.profit_target is None
    assert detail.analysis is None
    assert detail.news_links.investor_relations == "https://investor.apple.com"
    assert detail.news_links.yahoo_finance == "https://finance.yahoo.com/quote/AAPL"


def test_insufficient_history_has_no_chart_but_reports_countdown(db) -> None:
    stock = make_stock(db, "RIVN", "Rivian Automotive, Inc.")
    make_daily_prices(db, stock, ["13.00"] * 14)

    detail = get_stock_detail(db, "RIVN")

    assert detail.evaluation.status == "insufficient_history"
    assert detail.chart_days is None
    assert detail.thirty_day_average is None
    assert detail.days_required == 30
    assert detail.trading_days_until_ready == 16
    assert detail.evaluation.days_available == 14


def test_owned_position_includes_profit_target_progress(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["120.00"])
    db.add(
        Trade(stock_id=stock.id, action="buy", shares=Decimal(10), price_per_share=Decimal(100), trade_date=date(2026, 1, 1))
    )
    db.commit()
    set_position_target(db, "AAPL", Decimal("150.00"))

    detail = get_stock_detail(db, "AAPL")

    assert detail.user_avg_purchase_price == Decimal(100)
    assert detail.profit_target is not None
    assert detail.profit_target.target_dollars == Decimal("150.00")
    assert detail.profit_target.progress_dollars == Decimal("150.00")  # capped at target
    assert detail.profit_target.reached is True
    assert detail.effective_target_dollars == Decimal("150.00")


def test_investor_relations_url_may_be_null(db) -> None:
    stock = make_stock(db, "KO", "Coca-Cola Co.")
    make_daily_prices(db, stock, ["50.00"] * 30)
    detail = get_stock_detail(db, "KO")
    assert detail.news_links.investor_relations is None


def test_google_finance_link_includes_exchange_suffix_when_known(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.", exchange="NASDAQ")
    make_daily_prices(db, stock, ["50.00"] * 30)
    detail = get_stock_detail(db, "AAPL")
    assert detail.news_links.google_finance == "https://www.google.com/finance/quote/AAPL:NASDAQ"


def test_google_finance_link_omits_suffix_when_exchange_unknown(db) -> None:
    stock = make_stock(db, "KO", "Coca-Cola Co.", exchange=None)
    make_daily_prices(db, stock, ["50.00"] * 30)
    detail = get_stock_detail(db, "KO")
    assert detail.news_links.google_finance == "https://www.google.com/finance/quote/KO"


def test_analysis_included_when_set(db) -> None:
    stock = make_stock(db, "AAPL", "Apple Inc.")
    make_daily_prices(db, stock, ["100.00"] * 29 + ["90.00"])
    set_analysis(db, "AAPL", date(2026, 8, 20), Decimal("210.00"))

    detail = get_stock_detail(db, "AAPL")

    assert detail.analysis is not None
    assert detail.analysis.date == date(2026, 8, 20)
    assert detail.analysis.value == Decimal("210.00")
    assert detail.analysis_progress is not None
    assert detail.analysis_progress.target_price == Decimal("210.00")
    assert detail.analysis_progress.reached is False


def test_analysis_progress_is_none_when_current_price_unknown(db) -> None:
    make_stock(db, "RIVN", "Rivian Automotive, Inc.")  # never refreshed, no current price
    set_analysis(db, "RIVN", date(2026, 8, 20), Decimal("15.00"))

    detail = get_stock_detail(db, "RIVN")

    assert detail.analysis is not None
    assert detail.analysis_progress is None


def test_analysis_present_regardless_of_ownership(db) -> None:
    make_stock(db, "RIVN", "Rivian Automotive, Inc.")  # no trades, no history
    set_analysis(db, "RIVN", date(2026, 8, 20), Decimal("15.00"))

    detail = get_stock_detail(db, "RIVN")

    assert detail.evaluation.status == "insufficient_history"
    assert detail.evaluation.position is None
    assert detail.analysis is not None
    assert detail.analysis.value == Decimal("15.00")
