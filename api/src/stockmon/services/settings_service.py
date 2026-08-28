from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from stockmon.db.models import ProfitTarget, Settings, Stock
from stockmon.services.stock_service import StockNotFoundError

DEFAULT_TARGET = Decimal("50.00")
SETTINGS_ID = 1


@dataclass(frozen=True)
class SettingsView:
    default_profit_target_dollars: Decimal
    per_position_targets: dict[str, Decimal]


def _get_or_create_settings(db: Session) -> Settings:
    settings = db.get(Settings, SETTINGS_ID)
    if settings is None:
        settings = Settings(id=SETTINGS_ID, default_profit_target_dollars=DEFAULT_TARGET)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _build_view(db: Session, settings: Settings) -> SettingsView:
    overrides = (
        db.query(ProfitTarget, Stock.ticker).join(Stock, ProfitTarget.stock_id == Stock.id).all()
    )
    return SettingsView(
        default_profit_target_dollars=settings.default_profit_target_dollars,
        per_position_targets={ticker: target.target_dollars for target, ticker in overrides},
    )


def get_settings(db: Session) -> SettingsView:
    return _build_view(db, _get_or_create_settings(db))


def update_default_target(db: Session, target_dollars: Decimal) -> SettingsView:
    settings = _get_or_create_settings(db)
    settings.default_profit_target_dollars = target_dollars
    db.commit()
    return _build_view(db, settings)


def set_position_target(db: Session, ticker: str, target_dollars: Decimal) -> SettingsView:
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if stock is None:
        raise StockNotFoundError(ticker)

    override = db.get(ProfitTarget, stock.id)
    if override is None:
        db.add(ProfitTarget(stock_id=stock.id, target_dollars=target_dollars))
    else:
        override.target_dollars = target_dollars
    db.commit()

    return _build_view(db, _get_or_create_settings(db))


def remove_position_target(db: Session, ticker: str) -> SettingsView:
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if stock is None:
        raise StockNotFoundError(ticker)

    override = db.get(ProfitTarget, stock.id)
    if override is not None:
        db.delete(override)
        db.commit()

    return _build_view(db, _get_or_create_settings(db))


def get_effective_target(db: Session, stock_id: int) -> Decimal:
    override = db.get(ProfitTarget, stock_id)
    if override is not None:
        return override.target_dollars
    return _get_or_create_settings(db).default_profit_target_dollars
