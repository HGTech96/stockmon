from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stockmon.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    investor_relations_url: Mapped[str | None] = mapped_column(String(500))
    exchange: Mapped[str | None] = mapped_column(String(20))
    analysis_date: Mapped[date | None] = mapped_column(Date)
    analysis_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    daily_prices: Mapped[list["DailyPrice"]] = relationship(back_populates="stock")
    trades: Mapped[list["Trade"]] = relationship(back_populates="stock")
    profit_target: Mapped["ProfitTarget | None"] = relationship(back_populates="stock")


class DailyPrice(Base):
    __tablename__ = "daily_prices"
    __table_args__ = (UniqueConstraint("stock_id", "trade_date", name="uq_daily_price_stock_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    volume: Mapped[int] = mapped_column(BigInteger)

    stock: Mapped["Stock"] = relationship(back_populates="daily_prices")


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        CheckConstraint("shares > 0", name="ck_trade_shares_positive"),
        CheckConstraint("price_per_share > 0", name="ck_trade_price_positive"),
        CheckConstraint("action IN ('buy', 'sell')", name="ck_trade_action_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    action: Mapped[str] = mapped_column(String(4))
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    price_per_share: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    trade_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    stock: Mapped["Stock"] = relationship(back_populates="trades")


class Settings(Base):
    """Single-row table (id is always 1) — one local user, one settings record."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    default_profit_target_dollars: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("50.00"))


class ProfitTarget(Base):
    """Per-position override of the default profit target."""

    __tablename__ = "profit_targets"

    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), primary_key=True)
    target_dollars: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    stock: Mapped["Stock"] = relationship(back_populates="profit_target")


class CashEvent(Base):
    """External money in/out (deposit/withdraw), event-sourced like Trade --
    cash balance is derived by replaying these plus all trades, never stored
    as a mutable number."""

    __tablename__ = "cash_events"
    __table_args__ = (
        CheckConstraint("amount_usd > 0", name="ck_cash_event_amount_positive"),
        CheckConstraint("type IN ('deposit', 'withdraw')", name="ck_cash_event_type_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(8))
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    event_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScreenerResult(Base):
    """Latest screener run only -- scripts/run_screener.py truncates and
    rewrites this table in one transaction on every run. Not related to
    Stock: the screener universe (screener_stocks.txt) is a separate,
    unstored ticker list, never the tracked watchlist."""

    __tablename__ = "screener_results"
    __table_args__ = (UniqueConstraint("ticker", name="uq_screener_result_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    change_1d_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    change_7d_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    status: Mapped[str] = mapped_column(String(20))
    suggestion: Mapped[str | None] = mapped_column(String(4))
    conditions_met: Mapped[int | None] = mapped_column(Integer)
    conditions_total: Mapped[int | None] = mapped_column(Integer)
    rsi: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    price_vs_30d_avg_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    sharp_move: Mapped[bool | None] = mapped_column(Boolean)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class RefreshStatus(Base):
    """Single-row table (id is always 1) tracking the outcome of the most
    recent POST /api/refresh, used to compute the meta.isStale/dataAsOf
    fields on every GET response."""

    __tablename__ = "refresh_status"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    had_failures: Mapped[bool] = mapped_column(Boolean, default=False)
