from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stock import Envelope, ExchangeStatusOut, MoversOut, QuoteOut
from app.services import market_status
from app.services import stock_service as svc

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])


@router.get("", response_model=Envelope[list[QuoteOut]])
def market_indices(db: Session = Depends(get_db)):
    quotes = svc.index_quotes(db)
    return {"data": quotes, "meta": {"count": len(quotes)}}


@router.get("/status", response_model=Envelope[list[ExchangeStatusOut]])
def status():
    return {"data": market_status.exchange_status()}


@router.get("/movers", response_model=Envelope[MoversOut])
def get_movers(
    exchange: str | None = Query(None, description="For example JSE or NASDAQ"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    gainers, losers = svc.movers(db, exchange, limit)
    return {"data": {"gainers": gainers, "losers": losers}, "meta": {"basis": "latest close vs previous close"}}
