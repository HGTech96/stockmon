import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from stockmon.api.routes import portfolio, refresh, settings, stocks, trades
from stockmon.services.stock_service import StockNotFoundError
from stockmon.services.trade_service import TradeValidationError

app = FastAPI(title="stockmon")
app.include_router(refresh.router)
app.include_router(stocks.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(settings.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = "; ".join(str(error["msg"]) for error in exc.errors())
    return JSONResponse(status_code=422, content={"error": message})


@app.exception_handler(TradeValidationError)
def handle_trade_validation_error(request: Request, exc: TradeValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(StockNotFoundError)
def handle_stock_not_found_error(request: Request, exc: StockNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": str(exc)})


def main() -> None:
    uvicorn.run("stockmon.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
