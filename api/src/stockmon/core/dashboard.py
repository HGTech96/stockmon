from typing import Literal, Protocol, TypeVar

_SELL, _BUY, _WARNING_ONLY, _WAIT, _INSUFFICIENT = range(5)


class SortableStockRow(Protocol):
    ticker: str
    status: Literal["ok", "insufficient_history"]
    suggestion_label: Literal["BUY", "WAIT", "SELL"] | None
    has_warning: bool


T = TypeVar("T", bound=SortableStockRow)


def _bucket(row: SortableStockRow) -> int:
    if row.status == "insufficient_history":
        return _INSUFFICIENT
    if row.suggestion_label == "SELL":
        return _SELL
    if row.suggestion_label == "BUY":
        return _BUY
    if row.has_warning:
        return _WARNING_ONLY
    return _WAIT


def sort_dashboard_rows(rows: list[T]) -> list[T]:
    """Server-side dashboard order: SELL, BUY, warning-only (WAIT/no-suggestion
    with a warning), WAIT, then insufficient-history. Ticker-alphabetical
    tiebreak within a bucket."""
    return sorted(rows, key=lambda row: (_bucket(row), row.ticker))
