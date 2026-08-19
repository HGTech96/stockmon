from decimal import Decimal

from stockmon.api.schemas.base import CamelModel, Money
from stockmon.services.settings_service import SettingsView


class SettingsResponse(CamelModel):
    default_profit_target_dollars: Money
    per_position_targets: dict[str, Money]

    @classmethod
    def from_core(cls, view: SettingsView) -> "SettingsResponse":
        return cls(
            default_profit_target_dollars=view.default_profit_target_dollars,
            per_position_targets=view.per_position_targets,
        )


class UpdateDefaultTargetRequest(CamelModel):
    default_profit_target_dollars: Decimal


class UpdatePositionTargetRequest(CamelModel):
    target_dollars: Decimal
