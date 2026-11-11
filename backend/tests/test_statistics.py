import numpy as np
import pandas as pd
import pytest

from app.analytics.statistics import analyse, correlograms, histogram, qq, summary_stats


def prices_from_returns_pct(r):
    idx = pd.date_range("2020-01-01", periods=len(r) + 1, freq="B")
    return pd.Series(100 * np.exp(np.concatenate([[0], np.cumsum(np.asarray(r) / 100)])), index=idx)


def garch_returns(n=2000, seed=1, omega=0.05, alpha=0.2, beta=0.75):
    rng = np.random.default_rng(seed)
    r, var = np.zeros(n), omega / (1 - alpha - beta)
    for t in range(n):
        r[t] = np.sqrt(var) * rng.standard_normal()
        var = omega + alpha * r[t] ** 2 + beta * var
    return r


def by_id(result):
    return {t["id"]: t for t in result["tests"]}


@pytest.fixture(scope="module")
def white_noise():
    return analyse(prices_from_returns_pct(np.random.default_rng(0).normal(0, 1, 1500)))


@pytest.fixture(scope="module")
def clustered():
    return analyse(prices_from_returns_pct(garch_returns()))


def test_white_noise_returns_are_stationary_and_look_normal(white_noise):
    t = by_id(white_noise)
    assert t["adf_returns"]["reject_null"] and t["adf_returns"]["p_value"] < 0.001
    assert not t["jarque_bera"]["reject_null"]
    assert not t["arch_lm"]["reject_null"]
    assert not t["ljung_box_returns"]["reject_null"]


def test_random_walk_log_price_has_unit_root(white_noise):
    assert not by_id(white_noise)["adf_log_price"]["reject_null"]


def test_garch_data_shows_volatility_clustering(clustered):
    t = by_id(clustered)
    assert t["arch_lm"]["reject_null"] and t["arch_lm"]["p_value"] < 0.001
    assert t["ljung_box_squared"]["reject_null"]
    assert t["jarque_bera"]["reject_null"]  # GARCH with normal shocks is still fat tailed


def test_student_t_returns_reject_normality():
    r = np.random.default_rng(3).standard_t(3, 1500)
    assert by_id(analyse(prices_from_returns_pct(r)))["jarque_bera"]["reject_null"]


def test_every_test_reports_statistic_pvalue_and_reading(white_noise):
    assert len(white_noise["tests"]) == 6
    for t in white_noise["tests"]:
        assert 0.0 <= t["p_value"] <= 1.0 and np.isfinite(t["statistic"])
        assert t["interpretation"].startswith(("Evidence against", "Insufficient evidence"))
        assert t["alpha"] == 0.05
        assert "pass" not in t["interpretation"].lower() and "fail" not in t["interpretation"].lower()


def test_adf_details_include_critical_values(white_noise):
    d = by_id(white_noise)["adf_returns"]["details"]
    assert d["critical_value_1pct"] < d["critical_value_5pct"] < d["critical_value_10pct"] < 0


def test_summary_stats_match_numpy():
    x = np.random.default_rng(5).normal(0.05, 1.2, 800)
    s = summary_stats(x)
    assert s["observations"] == 800 and s["mean_pct"] == pytest.approx(x.mean())
    assert s["std_pct"] == pytest.approx(x.std(ddof=1)) and s["median_pct"] == pytest.approx(np.median(x))


def test_histogram_density_integrates_to_one():
    h = histogram(np.random.default_rng(6).normal(0, 1, 2000), bins=40)
    assert sum(h["density"]) * h["bin_width"] == pytest.approx(1.0, abs=1e-3)
    assert len(h["bin_centers"]) == len(h["normal_density"]) == 40


def test_qq_of_normal_data_lies_near_the_line():
    q = qq(np.random.default_rng(7).normal(0, 1, 3000))
    gap = np.abs(np.array(q["theoretical"]) - np.array(q["sample"]))
    assert np.median(gap) < 0.05 and np.all(np.diff(q["theoretical"]) > 0)


def test_correlogram_lengths_and_bound():
    c = correlograms(np.random.default_rng(8).normal(size=500), 30)
    assert c["lags"][0] == 1 and len(c["lags"]) == len(c["returns"]) == len(c["pacf_returns"]) == 30
    assert c["confidence_bound"] == pytest.approx(1.96 / np.sqrt(500))


def test_correlogram_is_capped_for_short_series():
    c = correlograms(np.random.default_rng(9).normal(size=60), 30)
    assert len(c["lags"]) == 29
