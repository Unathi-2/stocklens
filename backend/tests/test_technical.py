import numpy as np
import pandas as pd
import pytest

from app.analytics.performance import cumulative_return_pct, summarise
from app.analytics.technical import ema, sma


def series(values):
    return pd.Series(values, index=pd.date_range("2026-01-05", periods=len(values), freq="B"), dtype=float)


def test_sma_values_and_warm_up():
    out = sma(series([1, 2, 3, 4, 5]), 3)
    assert out.isna().sum() == 2
    assert out.iloc[2] == pytest.approx(2.0) and out.iloc[4] == pytest.approx(4.0)


def test_ema_matches_recursive_definition():
    out = ema(series([10, 11, 12, 13]), 3)  # alpha = 0.5
    e0 = 10.0
    e1 = 0.5 * 11 + 0.5 * e0
    e2 = 0.5 * 12 + 0.5 * e1
    e3 = 0.5 * 13 + 0.5 * e2
    assert out.iloc[:2].isna().all()
    assert out.iloc[2] == pytest.approx(e2) and out.iloc[3] == pytest.approx(e3)


def test_cumulative_return_starts_at_zero():
    out = cumulative_return_pct(series([100, 110, 99]))
    assert out.iloc[0] == 0.0 and out.iloc[1] == pytest.approx(10.0) and out.iloc[2] == pytest.approx(-1.0)


def test_summary_of_constant_growth_has_zero_volatility():
    prices = series([100 * 1.01**n for n in range(30)])
    s = summarise(prices)
    assert s["observations"] == 29
    assert s["annualised_volatility_pct"] == pytest.approx(0.0, abs=1e-9)
    assert s["mean_daily_return_pct"] == pytest.approx(np.log(1.01) * 100)
    assert s["total_return_pct"] == pytest.approx((1.01**29 - 1) * 100)


def test_summary_best_and_worst_day():
    s = summarise(series([100, 110, 99, 100]))
    assert s["best_day"][1] == pytest.approx(np.log(1.1) * 100)
    assert s["worst_day"][1] == pytest.approx(np.log(99 / 110) * 100)
    assert s["best_day"][0] < s["worst_day"][0]
