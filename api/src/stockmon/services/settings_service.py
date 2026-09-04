from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from stockmon.db.models import ProfitTarget, Settings, Ticker, WatchlistEntry
from stockmon.services.stock_service import get_watchlist_entry

DEFAULT_TARGET = Decimal("50.00")


@dataclass(frozen=True)
class SettingsView:
    default_profit_target_dollars: Decimal
    per_position_targets: dict[str, Decimal]


def _get_or_create_settings(db: Session, user_id: int) -> Settings:
    settings = db.get(Settings, user_id)
    if settings is None:
        settings = Settings(user_id=user_id, default_profit_target_dollars=DEFAULT_TARGET)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _build_view(db: Session, user_id: int, settings: Settings) -> SettingsView:
    overrides = (
        db.query(ProfitTarget, Ticker.ticker)
        .join(WatchlistEntry, ProfitTarget.watchlist_entry_id == WatchlistEntry.id)
        .join(Ticker, WatchlistEntry.ticker_id == Ticker.id)
        .filter(WatchlistEntry.user_id == user_id)
        .all()
    )
    return SettingsView(
        default_profit_target_dollars=settings.default_profit_target_dollars,
        per_position_targets={ticker: target.target_dollars for target, ticker in overrides},
    )


def get_settings(db: Session, user_id: int) -> SettingsView:
    return _build_view(db, user_id, _get_or_create_settings(db, user_id))


def update_default_target(db: Session, user_id: int, target_dollars: Decimal) -> SettingsView:
    settings = _get_or_create_settings(db, user_id)
    settings.default_profit_target_dollars = target_dollars
    db.commit()
    return _build_view(db, user_id, settings)


def set_position_target(db: Session, user_id: int, ticker: str, target_dollars: Decimal) -> SettingsView:
    entry = get_watchlist_entry(db, user_id, ticker)

    override = db.get(ProfitTarget, entry.id)
    if override is None:
        db.add(ProfitTarget(watchlist_entry_id=entry.id, target_dollars=target_dollars))
    else:
        override.target_dollars = target_dollars
    db.commit()

    return _build_view(db, user_id, _get_or_create_settings(db, user_id))


def remove_position_target(db: Session, user_id: int, ticker: str) -> SettingsView:
    entry = get_watchlist_entry(db, user_id, ticker)

    override = db.get(ProfitTarget, entry.id)
    if override is not None:
        db.delete(override)
        db.commit()

    return _build_view(db, user_id, _get_or_create_settings(db, user_id))


def get_effective_target(db: Session, watchlist_entry_id: int) -> Decimal:
    override = db.get(ProfitTarget, watchlist_entry_id)
    if override is not None:
        return override.target_dollars
    entry = db.get(WatchlistEntry, watchlist_entry_id)
    return _get_or_create_settings(db, entry.user_id).default_profit_target_dollars
