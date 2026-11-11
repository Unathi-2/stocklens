import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from app.analytics import risk


def prices_from_log_returns(r_pct, seed_price=100.0):
    idx = pd.date_range("2020-01-01", periods=len(r_pct) + 1, freq="B")
    return pd.Series(seed_price * np.exp(np.concatenate([[0], np.cumsum(np.asarray(r_pct) / 100)])), index=idx)


def garch_returns(n=3000, seed=3, omega=0.05, alpha=0.1, beta=0.85):
    rng = np.random.default_rng(seed)
    r, var = np.zeros(n), omega / (1 - alpha - beta)
    for t in range(n):
        r[t] = np.sqrt(var) * rng.standard_normal()
        var = omega + alpha * r[t] ** 2 + beta * var
    return r


def test_drawdown_known_path():
    idx = pd.date_range("2024-01-01", periods=7, freq="B")
    p = pd.Series([100, 120, 90, 60, 90, 120, 130], index=idx, dtype=float)
    d = risk.drawdown_detail(p)
    assert d["max_drawdown_pct"] == pytest.approx(-50.0)
    assert d["peak_date"] == idx[1].date() and d["trough_date"] == idx[3].date()
    assert d["recovery_date"] == idx[5].date()
    assert d["current_drawdown_pct"] == 0.0
    assert d["longest_underwater_days"] == 3  # 90, 60, 90 are below the 120 peak; 120 is back at it
    assert risk.drawdown_series(p).max() == 0.0


def test_drawdown_unrecovered_and_monotonic():
    idx = pd.date_range("2024-01-01", periods=4, freq="B")
    down = pd.Series([100, 80, 70, 75], index=idx, dtype=float)
    d = risk.drawdown_detail(down)
    assert d["recovery_date"] is None and d["current_drawdown_pct"] == pytest.approx(-25.0)
    up = pd.Series([1, 2, 3, 4], index=idx, dtype=float)
    d = risk.drawdown_detail(up)
    assert d["max_drawdown_pct"] == 0 and d["peak_date"] is None and d["longest_underwater_days"] == 0


def test_var_matches_normal_theory_on_normal_data():
    r = pd.Series(np.random.default_rng(0).normal(0.0004, 0.01, 50_000))
    v = risk.value_at_risk(r, 0.99)
    expected = -(0.0004 + stats.norm.ppf(0.01) * 0.01) * 100
    assert v["normal_var_pct"] == pytest.approx(expected, rel=0.02)
    assert v["historical_var_pct"] == pytest.approx(v["normal_var_pct"], rel=0.03)
    assert v["cornish_fisher_var_pct"] == pytest.approx(v["normal_var_pct"], rel=0.03)


def test_es_exceeds_var_and_99_exceeds_95():
    r = pd.Series(np.random.default_rng(1).standard_t(4, 5000) * 0.01)
    v95, v99 = (risk.value_at_risk(r, c) for c in (0.95, 0.99))
    for v in (v95, v99):
        assert v["historical_es_pct"] > v["historical_var_pct"] > 0
        assert v["normal_es_pct"] > v["normal_var_pct"] > 0
    assert v99["historical_var_pct"] > v95["historical_var_pct"]
    # fat tails: the normal model understates 99% VaR, Cornish-Fisher moves toward the data
    assert v99["cornish_fisher_var_pct"] > v99["normal_var_pct"]


def test_kupiec_accepts_iid_and_rejects_a_bad_model():
    r = pd.Series(np.random.default_rng(5).normal(0, 0.01, 2000))
    b = risk.kupiec_backtest(r, 0.95)
    assert b["tests"] == 2000 - 250
    assert b["violations"] == pytest.approx(b["expected_violations"], abs=0.35 * b["expected_violations"])
    assert not b["reject_null"]
    # volatility doubles out of sample, so a window built on calm data under-predicts risk
    calm_then_wild = pd.Series(np.concatenate([np.random.default_rng(6).normal(0, 0.005, 500),
                                               np.random.default_rng(7).normal(0, 0.02, 1500)]))
    assert risk.kupiec_backtest(calm_then_wild, 0.99)["reject_null"]


def test_kupiec_needs_enough_history():
    assert risk.kupiec_backtest(pd.Series(np.random.default_rng(0).normal(0, 0.01, 300)), 0.95) is None


def test_ratios_basic_properties():
    p = prices_from_log_returns(np.random.default_rng(2).normal(0.05, 1.0, 1000))
    a = risk.ratios(p, 0.0)
    b = risk.ratios(p, 8.0)
    assert a["sharpe"] > b["sharpe"]  # a higher risk free rate lowers excess return
    assert a["sortino"] > 0 and a["calmar"] > 0
    assert a["annualised_volatility_pct"] == pytest.approx(16.0, rel=0.1)
    assert a["downside_deviation_pct"] < a["annualised_volatility_pct"] * 1.1


def test_rolling_volatility_constant_variance():
    p = prices_from_log_returns(np.random.default_rng(3).normal(0, 1.0, 600))
    v = risk.rolling_volatility(p, 63)
    assert len(v) == 600 - 63 + 1
    assert v.mean() == pytest.approx(math.sqrt(252), rel=0.08)


def test_garch_recovers_parameters():
    g = risk.garch11(pd.Series(garch_returns()))
    assert g["converged"]
    by = {x["name"]: x["estimate"] for x in g["parameters"]}
    assert by["alpha"] == pytest.approx(0.10, abs=0.04)
    assert by["beta"] == pytest.approx(0.85, abs=0.07)
    assert g["persistence"] == pytest.approx(0.95, abs=0.04)
    assert g["half_life_days"] > 5
    assert len(g["volatility"]) == 3000


def test_garch_skipped_on_short_samples():
    assert risk.garch11(pd.Series(garch_returns(300))) is None


def test_analyse_output_is_json_safe():
    out = risk.analyse(prices_from_log_returns(garch_returns(800)), 7.0)
    assert set(out) == {"summary", "drawdown", "rolling_volatility", "var", "backtests", "garch"}
    assert [v["confidence"] for v in out["var"]] == [0.95, 0.99]
    assert len(out["backtests"]) == 2
