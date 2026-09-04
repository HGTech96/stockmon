from stockmon.api.schemas.base import CamelModel
from stockmon.services.stock_service import AddStockResult


class AddStockRequest(CamelModel):
    ticker: str


class AddStockResponse(CamelModel):
    ticker: str
    company_name: str
    history_fetched: bool

    @classmethod
    def from_core(cls, result: AddStockResult) -> "AddStockResponse":
        return cls(
            ticker=result.entry.ticker.ticker,
            company_name=result.entry.ticker.company_name,
            history_fetched=result.history_fetched,
        )
