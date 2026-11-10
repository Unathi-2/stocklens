"""Technical indicators. Pure functions on pandas Series, no web or database code."""
import pandas as pd


def sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple moving average. The first window - 1 values are NaN."""
    return prices.rolling(window=window, min_periods=window).mean()


def ema(prices: pd.Series, span: int) -> pd.Series:
    """Exponential moving average with alpha = 2 / (span + 1), seeded with the first price.
    Values are NaN until span observations exist, so every point has a full warm up."""
    return prices.ewm(span=span, adjust=False, min_periods=span).mean()
