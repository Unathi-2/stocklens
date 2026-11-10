import numpy as np
import pandas as pd

from app.analytics.returns import annualised_volatility, log_returns, max_drawdown


def test_log_return_single_step():
    r = log_returns(pd.Series([100.0, 110.0]))
    assert round(float(r.iloc[0]), 8) == round(float(np.log(1.1)), 8)


def test_constant_prices_have_zero_volatility():
    r = log_returns(pd.Series([50.0] * 10))
    assert annualised_volatility(r) == 0.0


def test_max_drawdown():
    prices = pd.Series([100.0, 120.0, 90.0, 110.0])
    assert round(max_drawdown(prices), 6) == round((90 - 120) / 120, 6)
