from datetime import date
from typing import Generic, Literal, TypeVar

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
    currency: str
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


class PointOut(BaseModel):
    date: date
    value: float


class IndicatorOut(BaseModel):
    name: str
    kind: Literal["sma", "ema"]
    window: int
    points: list[PointOut]


class DayValueOut(BaseModel):
    date: date
    value: float


class PerformanceSummaryOut(BaseModel):
    start_date: date
    end_date: date
    observations: int
    total_return_pct: float
    annualised_volatility_pct: float
    mean_daily_return_pct: float
    best_day: DayValueOut
    worst_day: DayValueOut


class PerformanceOut(BaseModel):
    summary: PerformanceSummaryOut
    cumulative_return: list[PointOut]
    daily_returns: list[PointOut]
