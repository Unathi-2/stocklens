from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, markets, stocks
from app.core.config import settings
from app.core.errors import register_error_handlers

app = FastAPI(
    title="StockLens API",
    version="0.2.0",
    description="Market data and analytics for JSE and US equities. Analytics only, not financial advice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(health.router)
app.include_router(stocks.router)
app.include_router(markets.router)
