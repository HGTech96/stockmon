from dataclasses import dataclass
from typing import Literal

from stockmon.core.dashboard import sort_dashboard_rows


@dataclass(frozen=True)
class _Row:
    ticker: str
    status: Literal["ok", "insufficient_history"] = "ok"
    suggestion_label: Literal["BUY", "WAIT", "SELL"] | None = "WAIT"
    has_warning: bool = False


def test_sell_before_buy_before_warning_before_wait_before_insufficient() -> None:
    rows = [
        _Row(ticker="WAIT1", suggestion_label="WAIT"),
        _Row(ticker="INSUFF1", status="insufficient_history", suggestion_label=None),
        _Row(ticker="WARN1", suggestion_label="WAIT", has_warning=True),
        _Row(ticker="BUY1", suggestion_label="BUY"),
        _Row(ticker="SELL1", suggestion_label="SELL"),
    ]
    sorted_rows = sort_dashboard_rows(rows)
    assert [r.ticker for r in sorted_rows] == ["SELL1", "BUY1", "WARN1", "WAIT1", "INSUFF1"]


def test_sell_with_warning_stays_in_sell_bucket() -> None:
    rows = [
        _Row(ticker="WAIT1", suggestion_label="WAIT"),
        _Row(ticker="SELLWARN", suggestion_label="SELL", has_warning=True),
    ]
    sorted_rows = sort_dashboard_rows(rows)
    assert [r.ticker for r in sorted_rows] == ["SELLWARN", "WAIT1"]


def test_ticker_alphabetical_tiebreak_within_bucket() -> None:
    rows = [
        _Row(ticker="TSLA", suggestion_label="BUY"),
        _Row(ticker="AAPL", suggestion_label="BUY"),
        _Row(ticker="MSFT", suggestion_label="BUY"),
    ]
    sorted_rows = sort_dashboard_rows(rows)
    assert [r.ticker for r in sorted_rows] == ["AAPL", "MSFT", "TSLA"]


def test_insufficient_history_always_last_even_with_warning_flag() -> None:
    rows = [
        _Row(ticker="INSUFF", status="insufficient_history", suggestion_label=None, has_warning=True),
        _Row(ticker="WAIT1", suggestion_label="WAIT"),
    ]
    sorted_rows = sort_dashboard_rows(rows)
    assert [r.ticker for r in sorted_rows] == ["WAIT1", "INSUFF"]
