import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from stockmon.api.deps import NotAuthenticatedError
from stockmon.api.routes import auth, cash, portfolio, refresh, screener, settings, stocks, trades
from stockmon.config import settings as app_settings
from stockmon.services.auth_service import InvalidCredentialsError, UsernameTakenError
from stockmon.services.cash_service import CashNotFoundError, CashValidationError
from stockmon.services.stock_service import StockAlreadyOnWatchlistError, StockNotFoundError, UnknownTickerError
from stockmon.services.trade_service import TradeNotFoundError, TradeValidationError

app = FastAPI(title="stockmon")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[app_settings.ui_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(refresh.router)
app.include_router(stocks.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(settings.router)
app.include_router(cash.router)
app.include_router(screener.router)


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


@app.exception_handler(UnknownTickerError)
def handle_unknown_ticker_error(request: Request, exc: UnknownTickerError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(StockAlreadyOnWatchlistError)
def handle_stock_already_on_watchlist_error(request: Request, exc: StockAlreadyOnWatchlistError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.exception_handler(TradeNotFoundError)
def handle_trade_not_found_error(request: Request, exc: TradeNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(CashValidationError)
def handle_cash_validation_error(request: Request, exc: CashValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(CashNotFoundError)
def handle_cash_not_found_error(request: Request, exc: CashNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(NotAuthenticatedError)
def handle_not_authenticated_error(request: Request, exc: NotAuthenticatedError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"error": str(exc)})


@app.exception_handler(InvalidCredentialsError)
def handle_invalid_credentials_error(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"error": str(exc)})


@app.exception_handler(UsernameTakenError)
def handle_username_taken_error(request: Request, exc: UsernameTakenError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"error": str(exc)})


def main() -> None:
    # uvicorn's reload spawns a subprocess by reconstructing sys.argv, which
    # is PyCharm's pydevd launcher (not this script) when running under the
    # debugger -- that reconstruction breaks, so disable reload in that case.
    debugging = "pydevd" in sys.modules or sys.gettrace() is not None
    uvicorn.run("stockmon.main:app", host="0.0.0.0", port=8000, reload=not debugging)


if __name__ == "__main__":
    main()
