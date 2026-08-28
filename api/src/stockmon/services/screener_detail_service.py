from decimal import Decimal

from stockmon.core.evaluation import detect_sharp_move, evaluate_entry
from stockmon.core.indicators import (
    MIN_HISTORY_DAYS,
    InsufficientHistoryError,
    calculate_indicators,
    calculate_price_snapshot,
)
from stockmon.core.market_data import MarketDataError, MarketDataProvider
from stockmon.db.models import Stock
from stockmon.services.refresh_service import DEFAULT_HISTORY_DAYS, overlay_live_price
from stockmon.services.stock_detail_service import ChartDay, StockDetail, news_links_for_ticker
from stockmon.services.stock_service import StockEvaluation, Status, UnknownTickerError


def get_screener_stock_detail(provider: MarketDataProvider, ticker: str) -> StockDetail:
    """Live-fetch one ticker's history and evaluate it with the same core
    functions the DB-backed tracked detail uses -- nothing is read from or
    written to the DB. Screener stocks are never owned, so position is
    always None; that's what makes reusing StockDetail/StockDetailResponse
    unchanged possible."""
    ticker = ticker.strip().upper()

    try:
        company_name = provider.fetch_company_name(ticker).strip()
    except MarketDataError as exc:
        raise UnknownTickerError(ticker) from exc
    if not company_name:
        raise UnknownTickerError(ticker)

    try:
        bars = provider.fetch_daily_history(ticker, DEFAULT_HISTORY_DAYS)
    except MarketDataError:
        # A resolvable ticker with no usable price data yet -- not a 422,
        # same insufficient_history state a freshly-tracked stock can be in.
        bars = []
    bars = overlay_live_price(provider, ticker, bars)

    stock = Stock(ticker=ticker, company_name=company_name)

    status: Status = "insufficient_history"
    current_price = None
    change_1d_pct = None
    indicators = None
    try:
        indicators = calculate_indicators(bars)
        current_price = indicators.current_price
        change_1d_pct = indicators.change_1d_pct
        status = "ok"
    except InsufficientHistoryError:
        snapshot = calculate_price_snapshot(bars)
        if snapshot is not None:
            current_price = snapshot.current_price
            change_1d_pct = snapshot.change_1d_pct

    suggestion = evaluate_entry(indicators) if indicators is not None else None
    warning = detect_sharp_move(indicators) if indicators is not None else None

    evaluation = StockEvaluation(
        stock=stock,
        bars=bars,
        status=status,
        current_price=current_price,
        change_1d_pct=change_1d_pct,
        indicators=indicators,
        days_available=len(bars),
        position=None,
        position_value=None,
        suggestion=suggestion,
        warning=warning,
    )

    chart_days: list[ChartDay] | None = None
    thirty_day_average: Decimal | None = None
    trading_days_until_ready: int | None = None
    if status == "ok":
        assert indicators is not None
        window = bars[-MIN_HISTORY_DAYS:]
        chart_days = [ChartDay(date=bar.date, close=bar.close, volume=bar.volume) for bar in window]
        thirty_day_average = indicators.thirty_day_average
    else:
        trading_days_until_ready = MIN_HISTORY_DAYS - len(bars)

    return StockDetail(
        evaluation=evaluation,
        days_required=MIN_HISTORY_DAYS,
        trading_days_until_ready=trading_days_until_ready,
        chart_days=chart_days,
        thirty_day_average=thirty_day_average,
        user_avg_purchase_price=None,
        profit_target=None,
        effective_target_dollars=Decimal(0),  # unused: no position, so no profit_target is ever built
        analysis=None,  # screener tickers aren't on the watchlist, never have a stored analysis
        analysis_progress=None,
        news_links=news_links_for_ticker(ticker, None, provider.fetch_exchange(ticker)),
    )
