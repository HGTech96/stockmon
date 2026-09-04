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


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("username", name="uq_user_username"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")


class UserSession(Base):
    """Opaque bearer token stored server-side (not a JWT) -- login creates a
    row, logout deletes it, so revocation is just a DELETE. Fixed 30-day
    lifetime from creation, no sliding renewal. Named UserSession (table
    `sessions`) to avoid colliding with sqlalchemy.orm.Session, which every
    service function uses as the DB-session type hint."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")


class Ticker(Base):
    """Shared market-data identity for a symbol -- one row per ticker no
    matter how many users track it. Per-user fields (analysis note, trades,
    profit-target override) live on WatchlistEntry instead."""

    __tablename__ = "tickers"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    investor_relations_url: Mapped[str | None] = mapped_column(String(500))
    exchange: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    daily_prices: Mapped[list["DailyPrice"]] = relationship(back_populates="ticker")
    watchlist_entries: Mapped[list["WatchlistEntry"]] = relationship(back_populates="ticker")


class WatchlistEntry(Base):
    """"My tracked stock" -- one user's link to a shared Ticker. Owns the
    per-user analysis note; trades and the profit-target override key off
    this row's id, not the ticker's."""

    __tablename__ = "watchlist_entries"
    __table_args__ = (UniqueConstraint("user_id", "ticker_id", name="uq_watchlist_entry_user_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    analysis_date: Mapped[date | None] = mapped_column(Date)
    analysis_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticker: Mapped["Ticker"] = relationship(back_populates="watchlist_entries")
    trades: Mapped[list["Trade"]] = relationship(back_populates="watchlist_entry")
    profit_target: Mapped["ProfitTarget | None"] = relationship(back_populates="watchlist_entry")


class DailyPrice(Base):
    __tablename__ = "daily_prices"
    __table_args__ = (UniqueConstraint("ticker_id", "trade_date", name="uq_daily_price_ticker_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("tickers.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    volume: Mapped[int] = mapped_column(BigInteger)

    ticker: Mapped["Ticker"] = relationship(back_populates="daily_prices")


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        CheckConstraint("shares > 0", name="ck_trade_shares_positive"),
        CheckConstraint("price_per_share > 0", name="ck_trade_price_positive"),
        CheckConstraint("action IN ('buy', 'sell')", name="ck_trade_action_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    watchlist_entry_id: Mapped[int] = mapped_column(ForeignKey("watchlist_entries.id"), index=True)
    action: Mapped[str] = mapped_column(String(4))
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    price_per_share: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    trade_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    watchlist_entry: Mapped["WatchlistEntry"] = relationship(back_populates="trades")


class Settings(Base):
    """One row per user (user_id is the PK) -- was a single global singleton
    row before per-user accounts."""

    __tablename__ = "settings"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    default_profit_target_dollars: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("50.00"))


class ProfitTarget(Base):
    """Per-position override of the default profit target."""

    __tablename__ = "profit_targets"

    watchlist_entry_id: Mapped[int] = mapped_column(ForeignKey("watchlist_entries.id"), primary_key=True)
    target_dollars: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    watchlist_entry: Mapped["WatchlistEntry"] = relationship(back_populates="profit_target")


class CashEvent(Base):
    """External money in/out (deposit/withdraw), event-sourced like Trade --
    cash balance is derived by replaying these plus all trades, never stored
    as a mutable number. Per-user: each user has their own cash ledger."""

    __tablename__ = "cash_events"
    __table_args__ = (
        CheckConstraint("amount_usd > 0", name="ck_cash_event_amount_positive"),
        CheckConstraint("type IN ('deposit', 'withdraw')", name="ck_cash_event_type_valid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(8))
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    event_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScreenerResult(Base):
    """Latest screener run only -- scripts/run_screener.py truncates and
    rewrites this table in one transaction on every run. Not related to
    Ticker/WatchlistEntry: the screener universe (screener_stocks.txt) is a
    separate, unstored, global ticker list, never the tracked watchlist."""

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
    """One row per user (user_id is the PK), tracking the outcome of that
    user's most recent POST /api/refresh -- used to compute the
    meta.isStale/dataAsOf fields on every GET response. Was a single global
    singleton row before per-user accounts."""

    __tablename__ = "refresh_status"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    had_failures: Mapped[bool] = mapped_column(Boolean, default=False)
