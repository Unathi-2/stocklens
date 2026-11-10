from app.core.config import settings
from app.services.market_data import MarketDataProvider


def get_provider() -> MarketDataProvider:
    name = settings.market_data_provider.lower()
    if name == "yfinance":
        from app.services.providers.yfinance_provider import YFinanceProvider

        return YFinanceProvider()
    raise ValueError(f"Unknown market data provider: {name}")
