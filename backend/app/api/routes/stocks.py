from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import InvalidParameter
from app.schemas.stock import (
    BarOut, CompanyOut, Envelope, IndicatorOut, PerformanceOut, ProfileOut, QuoteOut, StatisticsOut,
)
from app.services import stock_service as svc

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])

ERRORS = {404: {"description": "Stock or price data not found"}, 409: {"description": "Symbol on several exchanges"}}
Period = Literal["1m", "3m", "6m", "1y", "5y", "max"]
Interval = Literal["1d", "1wk", "1mo"]
MAX_WINDOWS = 6


def parse_windows(raw: str, name: str) -> list[int]:
    """Turn "20,50,200" into [20, 50, 200], with limits that keep requests cheap."""
    if not raw.strip():
        return []
    try:
        values = [int(part) for part in raw.split(",") if part.strip()]
    except ValueError:
        raise InvalidParameter(f"{name} must be a comma separated list of whole numbers, for example 20,50,200.")
    if len(values) > MAX_WINDOWS:
        raise InvalidParameter(f"{name} accepts at most {MAX_WINDOWS} windows.")
    if any(v < 2 or v > 400 for v in values):
        raise InvalidParameter(f"Each {name} window must be between 2 and 400.")
    return values


Exchange = Query(None, description="Exchange filter, needed only when a symbol exists on several exchanges")


@router.get("/search", response_model=Envelope[list[CompanyOut]])
def search(
    q: str = Query(..., min_length=1, description="Part of a symbol or company name"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    results = svc.search_companies(db, q, limit)
    return {"data": results, "meta": {"count": len(results), "query": q}}


@router.get("/{symbol}", response_model=Envelope[CompanyOut], responses=ERRORS)
def get_stock(symbol: str, exchange: str | None = Exchange, db: Session = Depends(get_db)):
    return {"data": svc.find_company(db, symbol, exchange)}


@router.get("/{symbol}/profile", response_model=Envelope[ProfileOut], responses=ERRORS)
def get_profile(symbol: str, exchange: str | None = Exchange, db: Session = Depends(get_db)):
    company = svc.find_company(db, symbol, exchange)
    return {"data": svc.build_profile(db, company)}


@router.get("/{symbol}/quote", response_model=Envelope[QuoteOut], responses=ERRORS)
def get_quote(symbol: str, exchange: str | None = Exchange, db: Session = Depends(get_db)):
    company = svc.find_company(db, symbol, exchange)
    return {"data": svc.build_quote(db, company), "meta": {"source": "latest stored daily close"}}


@router.get("/{symbol}/history", response_model=Envelope[list[BarOut]], responses=ERRORS)
def get_history(
    symbol: str,
    period: Period = "1y",
    interval: Interval = "1d",
    start: date | None = Query(None, description="Overrides period when given"),
    end: date | None = None,
    exchange: str | None = Exchange,
    db: Session = Depends(get_db),
):
    company = svc.find_company(db, symbol, exchange)
    bars = svc.get_history(db, company, period, interval, start, end)
    return {
        "data": bars,
        "meta": {"count": len(bars), "period": period, "interval": interval, "currency": company.currency},
    }


@router.get("/{symbol}/indicators", response_model=Envelope[list[IndicatorOut]], responses=ERRORS)
def get_indicators(
    symbol: str,
    period: Period = "1y",
    interval: Interval = "1d",
    start: date | None = Query(None, description="Overrides period when given"),
    end: date | None = None,
    sma: str = Query("20,50,200", description="Simple moving average windows, comma separated"),
    ema: str = Query("20", description="Exponential moving average spans, comma separated"),
    exchange: str | None = Exchange,
    db: Session = Depends(get_db),
):
    sma_windows = parse_windows(sma, "sma")
    ema_windows = parse_windows(ema, "ema")
    company = svc.find_company(db, symbol, exchange)
    series = svc.get_indicators(db, company, period, interval, start, end, sma_windows, ema_windows)
    return {"data": series, "meta": {"price_basis": "close", "interval": interval}}


@router.get("/{symbol}/performance", response_model=Envelope[PerformanceOut], responses=ERRORS)
def get_performance(
    symbol: str,
    period: Period = "1y",
    start: date | None = Query(None, description="Overrides period when given"),
    end: date | None = None,
    exchange: str | None = Exchange,
    db: Session = Depends(get_db),
):
    company = svc.find_company(db, symbol, exchange)
    result = svc.get_performance(db, company, period, start, end)
    return {
        "data": result,
        "meta": {"price_basis": "adjusted close", "return_type": "log", "trading_days_per_year": 252},
    }


@router.get("/{symbol}/statistics", response_model=Envelope[StatisticsOut], responses=ERRORS)
def get_statistics(
    symbol: str,
    period: Period = "5y",
    start: date | None = Query(None, description="Overrides period when given"),
    end: date | None = None,
    exchange: str | None = Exchange,
    db: Session = Depends(get_db),
):
    company = svc.find_company(db, symbol, exchange)
    result = svc.get_statistics(db, company, period, start, end)
    return {
        "data": result,
        "meta": {
            "price_basis": "adjusted close",
            "return_type": "log, in percent",
            "significance_level": 0.05,
            "minimum_observations": 60,
        },
    }
