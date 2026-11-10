"""Provider abstraction for market data.

Routes and services depend on MarketDataProvider only, so the data source
(yfinance for prototyping, a paid API later) can change without touching
the rest of the application. Implementations arrive in Phase 3.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class SymbolMatch:
    symbol: str
    name: str
    exchange: str


@dataclass
class PriceBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int


class MarketDataProvider(ABC):
    @abstractmethod
    def search_symbols(self, query: str) -> list[SymbolMatch]: ...

    @abstractmethod
    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]: ...

    @abstractmethod
    def get_profile(self, symbol: str) -> dict: ...
