import os
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from stockmon.db.base import Base  # noqa: E402
from stockmon.db.models import CashEvent, DailyPrice, Ticker, User, WatchlistEntry  # noqa: E402
from stockmon.db.session import get_db  # noqa: E402
from stockmon.main import app  # noqa: E402
from stockmon.services.auth_service import create_user  # noqa: E402

DEFAULT_USERNAME = "testuser"
DEFAULT_PASSWORD = "password123"


@pytest.fixture(scope="session")
def test_engine():
    url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(url)
    # drop_all first: create_all only fills in missing tables, so a schema
    # change (renamed/retargeted columns) would otherwise silently keep the
    # stale table shape from a previous test run against this same DB.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(test_engine) -> Session:
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

    session = sessionmaker(bind=test_engine)()
    yield session
    session.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """Unauthenticated -- use this for auth-flow tests (login/logout/me,
    401 cases) and cross-user isolation tests that need to control login
    explicitly. Most route tests want `authed_client` instead."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def authed_client(client: TestClient, db: Session) -> TestClient:
    """Logged in as the default test user (DEFAULT_USERNAME) -- every route
    except /api/auth/* now requires a session, and most route tests only
    ever cared about a single implicit user, so authenticating here keeps
    those tests unchanged."""
    make_user(db)
    client.post("/api/auth/login", json={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD})
    return client


def make_user(db: Session, username: str = DEFAULT_USERNAME, password: str = DEFAULT_PASSWORD, email: str | None = None) -> User:
    """Idempotent by username so call sites don't need to care whether a
    (or *the default*) user already exists in this test."""
    existing = db.query(User).filter(User.username == username).first()
    if existing is not None:
        return existing
    return create_user(db, username, password, email)


def make_ticker(
    db: Session,
    ticker: str,
    company_name: str = "Test Company",
    investor_relations_url: str | None = None,
    exchange: str | None = None,
) -> Ticker:
    row = Ticker(
        ticker=ticker,
        company_name=company_name,
        investor_relations_url=investor_relations_url,
        exchange=exchange,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def make_stock(
    db: Session,
    ticker: str,
    company_name: str = "Test Company",
    investor_relations_url: str | None = None,
    exchange: str | None = None,
    user: User | None = None,
) -> WatchlistEntry:
    """Creates a shared Ticker + a WatchlistEntry linking it to `user`
    (defaults to the shared DEFAULT_USERNAME test user, matching the
    `client` fixture's login). Returns the WatchlistEntry -- its `.id` is
    the id trades/profit-target overrides key off; its `.ticker_id` is the
    id daily_prices keys off; `.ticker` is the related Ticker row."""
    user = user or make_user(db)
    ticker_row = make_ticker(db, ticker, company_name, investor_relations_url, exchange)
    entry = WatchlistEntry(user_id=user.id, ticker_id=ticker_row.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def make_deposit(
    db: Session,
    amount: str = "100000",
    event_date: date | None = None,
    user: User | None = None,
) -> CashEvent:
    """Seeds a deposit directly (bypassing the service layer, like make_stock
    does for Ticker/WatchlistEntry) so buy-side tests have enough cash
    available without every test needing its own precisely-sized deposit.
    Defaults to a large amount dated far in the past so it lands before any
    trade in a test, and to the shared default test user."""
    user = user or make_user(db)
    event = CashEvent(
        user_id=user.id,
        type="deposit",
        amount_usd=Decimal(amount),
        event_date=event_date or date(2000, 1, 1),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def make_daily_prices(
    db: Session,
    stock: Ticker | WatchlistEntry,
    closes: list[str],
    volumes: list[int] | None = None,
    start: date | None = None,
) -> list[DailyPrice]:
    """One bar per calendar day starting at `start` (default: far enough in
    the past that the last close lands "today"), open=high=low=close.
    Accepts either a Ticker (make_ticker) or a WatchlistEntry (make_stock)
    -- daily_prices keys off the ticker either way."""
    ticker_id = stock.id if isinstance(stock, Ticker) else stock.ticker_id
    start = start or (date.today() - timedelta(days=len(closes) - 1))
    volumes = volumes or [1_000_000] * len(closes)
    rows = []
    for i, (close_str, volume) in enumerate(zip(closes, volumes)):
        close = Decimal(close_str)
        row = DailyPrice(
            ticker_id=ticker_id,
            trade_date=start + timedelta(days=i),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=volume,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    return rows
