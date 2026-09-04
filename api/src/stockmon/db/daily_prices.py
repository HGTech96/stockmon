from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from stockmon.core.market_data import DailyBar
from stockmon.db.models import DailyPrice


def upsert_daily_prices(db: Session, ticker_id: int, bars: list[DailyBar]) -> int:
    if not bars:
        return 0

    rows = [
        {
            "ticker_id": ticker_id,
            "trade_date": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
        }
        for bar in bars
    ]

    stmt = pg_insert(DailyPrice).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_daily_price_ticker_date",
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
        },
    )
    db.execute(stmt)
    return len(rows)
