from datetime import date
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: dict = {}


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    exchange: str
    asset_type: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    currency: str
    market_cap: int | None = None


class ProfileOut(CompanyOut):
    data_start: date | None = None
    data_end: date | None = None
    observations: int = 0


class QuoteOut(BaseModel):
    symbol: str
    name: str
    exchange: str
    currency: str
    as_of: date
    price: float
    previous_close: float | None = None
    change: float | None = None
    change_pct: float | None = None
    open: float
    high: float
    low: float
    volume: int
    week52_high: float
    week52_low: float


class BarOut(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int


class MoverOut(BaseModel):
    symbol: str
    name: str
    exchange: str
    as_of: date
    price: float
    change_pct: float


class MoversOut(BaseModel):
    gainers: list[MoverOut]
    losers: list[MoverOut]


class ExchangeStatusOut(BaseModel):
    exchange: str
    is_open: bool
    local_time: str
    opens: str
    closes: str
    note: str
