from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
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
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 4))
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
