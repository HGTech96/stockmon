from datetime import datetime
from typing import Literal

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.core.evaluation import Suggestion, Warning
from stockmon.core.freshness import Freshness
from stockmon.core.money import MoneySummary
from stockmon.core.position import ProfitTargetProgress


class MetaSchema(CamelModel):
    data_as_of: datetime
    is_stale: bool
    stale_message: str | None

    @classmethod
    def from_core(cls, freshness: Freshness) -> "MetaSchema":
        return cls(
            data_as_of=freshness.data_as_of,
            is_stale=freshness.is_stale,
            stale_message=freshness.stale_message,
        )


class ChecklistItemSchema(CamelModel):
    id: str
    text: str
    passed: bool


class SuggestionSchema(CamelModel):
    label: Literal["BUY", "WAIT", "SELL"]
    type: Literal["entry", "exit"]
    met_count: int
    total_count: int
    checklist: list[ChecklistItemSchema]
    note: str | None

    @classmethod
    def from_core(cls, suggestion: Suggestion) -> "SuggestionSchema":
        checklist = [
            ChecklistItemSchema(id=item.id, text=item.text, passed=item.passed)
            for item in suggestion.checklist
        ]
        met_count = sum(1 for item in suggestion.checklist if item.passed)
        return cls(
            label=suggestion.label,
            type=suggestion.type,
            met_count=met_count,
            total_count=len(suggestion.checklist),
            checklist=checklist,
            note=suggestion.note,
        )


class WarningSchema(CamelModel):
    reason: Literal["1d_move", "7d_move"]
    text: str

    @classmethod
    def from_core(cls, warning: Warning) -> "WarningSchema":
        return cls(reason=warning.reason, text=warning.text)


class MoneySchema(CamelModel):
    cash_available: Money
    net_deposited: Money
    realized_earned: Money
    realized_lost: Money
    unrealized_gain_open: Money
    unrealized_loss_open: Money

    @classmethod
    def from_core(cls, summary: MoneySummary) -> "MoneySchema":
        return cls(
            cash_available=summary.cash_available,
            net_deposited=summary.net_deposited,
            realized_earned=summary.realized_earned,
            realized_lost=summary.realized_lost,
            unrealized_gain_open=summary.unrealized_gain_open,
            unrealized_loss_open=summary.unrealized_loss_open,
        )


class ProfitTargetSchema(CamelModel):
    target_dollars: Money
    progress_dollars: Money
    remaining_dollars: Money
    reached: bool

    @classmethod
    def from_core(cls, progress: ProfitTargetProgress) -> "ProfitTargetSchema":
        return cls(
            target_dollars=progress.target_dollars,
            progress_dollars=progress.progress_dollars,
            remaining_dollars=progress.remaining_dollars,
            reached=progress.reached,
        )
