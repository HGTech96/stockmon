from datetime import date
from decimal import Decimal
from typing import Literal

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.api.schemas.common import MetaSchema
from stockmon.db.models import CashEvent as CashEventRow
from stockmon.services.cash_service import CashEventEntry


class CashEventRequest(CamelModel):
    type: Literal["deposit", "withdraw"]
    amount_usd: Decimal
    date: date


class CashEventSchema(CamelModel):
    id: int
    type: Literal["deposit", "withdraw"]
    amount_usd: Money
    date: date

    @classmethod
    def from_core(cls, entry: CashEventEntry) -> "CashEventSchema":
        return cls(id=entry.id, type=entry.type, amount_usd=entry.amount_usd, date=entry.date)

    @classmethod
    def from_row(cls, row: CashEventRow) -> "CashEventSchema":
        return cls(id=row.id, type=row.type, amount_usd=row.amount_usd, date=row.event_date)


class CashListResponse(CamelModel):
    meta: MetaSchema
    cash_available: Money
    events: list[CashEventSchema]

    @classmethod
    def from_core(
        cls, meta: MetaSchema, entries: list[CashEventEntry], cash_available: Decimal
    ) -> "CashListResponse":
        return cls(
            meta=meta,
            cash_available=cash_available,
            events=[CashEventSchema.from_core(entry) for entry in entries],
        )


class CashEventResponse(CamelModel):
    event: CashEventSchema
    cash_available: Money

    @classmethod
    def from_core(cls, row: CashEventRow, cash_available: Decimal) -> "CashEventResponse":
        return cls(event=CashEventSchema.from_row(row), cash_available=cash_available)
