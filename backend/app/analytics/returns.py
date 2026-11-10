"""Pure analytics functions. No web or database code belongs in this package."""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def log_returns(prices: pd.Series) -> pd.Series:
    """r_t = ln(P_t / P_{t-1})."""
    return np.log(prices / prices.shift(1)).dropna()


def annualised_volatility(returns: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Sample standard deviation of returns scaled by sqrt(periods)."""
    return float(returns.std(ddof=1) * np.sqrt(periods))


def max_drawdown(prices: pd.Series) -> float:
    """Largest peak to trough decline, as a negative fraction."""
    running_max = prices.cummax()
    return float(((prices - running_max) / running_max).min())
