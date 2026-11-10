"""Domain errors and their HTTP mapping. Every error uses one JSON shape:
{"error": {"code": "...", "message": "..."}}"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class StockNotFound(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol


class AmbiguousSymbol(Exception):
    def __init__(self, symbol: str, exchanges: list[str]):
        self.symbol = symbol
        self.exchanges = exchanges


class NoPriceData(Exception):
    def __init__(self, symbol: str):
        self.symbol = symbol


def _body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StockNotFound)
    async def _not_found(_: Request, exc: StockNotFound):
        return JSONResponse(status_code=404, content=_body("stock_not_found", f"No stock with symbol {exc.symbol}."))

    @app.exception_handler(AmbiguousSymbol)
    async def _ambiguous(_: Request, exc: AmbiguousSymbol):
        msg = f"Symbol {exc.symbol} exists on several exchanges ({', '.join(exc.exchanges)}). Add ?exchange=."
        return JSONResponse(status_code=409, content=_body("ambiguous_symbol", msg))

    @app.exception_handler(NoPriceData)
    async def _no_data(_: Request, exc: NoPriceData):
        return JSONResponse(status_code=404, content=_body("no_price_data", f"No price data stored for {exc.symbol}."))
