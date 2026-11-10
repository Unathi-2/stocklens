"""Return based performance measures. Pure functions, no web or database code."""
import pandas as pd

from app.analytics.returns import annualised_volatility, log_returns


def cumulative_return_pct(prices: pd.Series) -> pd.Series:
    """Percentage change since the first price in the window."""
    return (prices / prices.iloc[0] - 1.0) * 100.0


def summarise(prices: pd.Series) -> dict:
    """Summary of a price window. Needs at least 3 prices.

    Returns are log returns in percent. Volatility is the sample standard deviation
    of daily log returns scaled by sqrt(252).
    """
    r = log_returns(prices)
    best, worst = r.idxmax(), r.idxmin()
    return {
        "start_date": prices.index[0].date(),
        "end_date": prices.index[-1].date(),
        "observations": int(len(r)),
        "total_return_pct": float((prices.iloc[-1] / prices.iloc[0] - 1.0) * 100.0),
        "annualised_volatility_pct": annualised_volatility(r) * 100.0,
        "mean_daily_return_pct": float(r.mean() * 100.0),
        "best_day": (best.date(), float(r[best] * 100.0)),
        "worst_day": (worst.date(), float(r[worst] * 100.0)),
    }
