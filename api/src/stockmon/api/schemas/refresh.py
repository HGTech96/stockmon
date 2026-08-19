from datetime import datetime

from stockmon.api.schemas.base import CamelModel


class RefreshFailureItem(CamelModel):
    ticker: str
    error: str


class RefreshResponse(CamelModel):
    refreshed: list[str]
    failed: list[RefreshFailureItem]
    data_as_of: datetime
