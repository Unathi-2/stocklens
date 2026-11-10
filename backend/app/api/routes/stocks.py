from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stock import BarOut, CompanyOut, Envelope, ProfileOut, QuoteOut
from app.services import stock_service as svc

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])

ERRORS = {404: {"description": "Stock or price data not found"}, 409: {"description": "Symbol on several exchanges"}}
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
    period: Literal["1m", "3m", "6m", "1y", "5y", "max"] = "1y",
    interval: Literal["1d", "1wk", "1mo"] = "1d",
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
