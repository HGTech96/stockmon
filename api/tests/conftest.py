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
from stockmon.db.models import DailyPrice, Stock  # noqa: E402
from stockmon.db.session import get_db  # noqa: E402
from stockmon.main import app  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():
    url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(url)
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
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_stock(
    db: Session,
    ticker: str,
    company_name: str = "Test Company",
    investor_relations_url: str | None = None,
) -> Stock:
    stock = Stock(ticker=ticker, company_name=company_name, investor_relations_url=investor_relations_url)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def make_daily_prices(
    db: Session,
    stock: Stock,
    closes: list[str],
    volumes: list[int] | None = None,
    start: date | None = None,
) -> list[DailyPrice]:
    """One bar per calendar day starting at `start` (default: far enough in
    the past that the last close lands "today"), open=high=low=close."""
    start = start or (date.today() - timedelta(days=len(closes) - 1))
    volumes = volumes or [1_000_000] * len(closes)
    rows = []
    for i, (close_str, volume) in enumerate(zip(closes, volumes)):
        close = Decimal(close_str)
        row = DailyPrice(
            stock_id=stock.id,
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
