import math

import numpy as np
import pandas as pd
import pytest

from app.analytics import evaluation as ev
from test_volatility import gjr_returns


def test_proxies_match_formulas():
    df = pd.DataFrame(
        {"open": [100.0, 100.0, 101.0], "high": [102.0, 103.0, 104.0], "low": [98.0, 99.0, 100.0],
         "close": [100.0, 102.0, 101.0], "adjusted_close": [100.0, 102.0, 101.0]},
        index=pd.date_range("2024-01-01", periods=3, freq="B"),
    )
    p = ev.variance_proxies(df)
    assert len(p["parkinson"]) == 2 and p["parkinson"].index[0] == df.index[1]
    assert p["parkinson"].iloc[0] == pytest.approx((math.log(103 / 99) * 100) ** 2 / (4 * math.log(2)))
    assert p["squared_return"].iloc[0] == pytest.approx((math.log(102 / 100) * 100) ** 2)
    gk = 0.5 * (math.log(103 / 99) * 100) ** 2 - (2 * math.log(2) - 1) * (math.log(102 / 100) * 100) ** 2
    assert p["garman_klass"].iloc[0] == pytest.approx(gk)


def test_rolling_forecasts_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="window must be an integer of at least 2"):
        ev.rolling_forecasts(pd.Series(np.ones(10)), window=0, refit_every=1)
    with pytest.raises(ValueError, match="refit_every must be a positive integer"):
        ev.rolling_forecasts(pd.Series(np.ones(10)), window=2, refit_every=0)
    with pytest.raises(ValueError, match="returns must contain only finite values"):
        ev.rolling_forecasts(pd.Series([1.0, 2.0, np.nan, 4.0]), window=2, refit_every=1)


def test_qlike_properties():
    px = np.array([1.0, 1.0, 1.0])
    h = np.array([1.0, 0.5, 2.0])
    q = ev.qlike(px, h)
    assert q[0] == pytest.approx(0.0)
    assert q[1] > q[2] > 0  # forecasting half the variance costs more than forecasting double
    assert ev.mse(px, h)[0] == 0


def test_diebold_mariano_detects_a_better_model():
    rng = np.random.default_rng(0)
    bench = rng.chisquare(1, 800) + 0.4
    better = rng.chisquare(1, 800)
    out = ev.diebold_mariano(bench, better)
    assert out["mean_difference"] > 0 and out["p_value"] < 0.01
    same = ev.diebold_mariano(bench, bench + rng.normal(0, 0.05, 800))
    assert same["p_value"] > 0.05
    assert ev.diebold_mariano(bench[:10], better[:10]) is None


def test_mcs_removes_the_bad_model_and_keeps_equals():
    rng = np.random.default_rng(1)
    n = 800
    common = rng.chisquare(1, n)
    L = np.column_stack([
        common + rng.normal(0, 0.1, n),
        common + rng.normal(0, 0.1, n),
        common + 0.5 + rng.normal(0, 0.1, n),  # clearly worse
    ])
    p = ev.model_confidence_set(L)
    assert p[2] < 0.10 and p[0] >= 0.10 and p[1] >= 0.10
    assert ev.model_confidence_set(L) .tolist() == p.tolist()  # deterministic


def test_mcs_keeps_everyone_when_models_are_equivalent():
    rng = np.random.default_rng(2)
    base = rng.chisquare(1, 600)
    L = np.column_stack([base + rng.normal(0, 0.2, 600) for _ in range(4)])
    assert (ev.model_confidence_set(L) >= 0.10).all()


@pytest.fixture(scope="module")
def rolled():
    r = pd.Series(gjr_returns(700, seed=9))
    return r, ev.rolling_forecasts(r, window=300, refit_every=200)


def test_rolling_forecasts_shape_and_levels(rolled):
    r, out = rolled
    assert out["forecast_start"] == 300
    for m, h in out["forecasts"].items():
        assert len(h) == 400 and np.isfinite(h).all() and (h > 0).all(), m
        assert h.mean() == pytest.approx(float(np.mean(r.to_numpy()[300:] ** 2)), rel=0.5), m
    assert sum(out["failures"].values()) == 0


def test_rolling_forecasts_are_causal(rolled):
    """Changing returns after a block must not change forecasts inside that block."""
    r, out = rolled
    r2 = r.copy()
    r2.iloc[520:] = r2.iloc[520:] * 5.0  # first block covers 300..499, second 500..699
    out2 = ev.rolling_forecasts(r2, window=300, refit_every=200)
    for m in out["forecasts"]:
        a, b = out["forecasts"][m][:200], out2["forecasts"][m][:200]
        assert np.allclose(a, b, rtol=1e-8), m
        # inside the second block the forecasts up to day 520 only depend on data before 520. FIGARCH in arch
        # sets its pre sample variance from the series it sees, a tiny dependence we allow for.
        tol = 5e-3 if m == "figarch" else 1e-8
        assert np.allclose(out["forecasts"][m][200:220], out2["forecasts"][m][200:220], rtol=tol), m


def make_payload(n=500, seed=3):
    rng = np.random.default_rng(seed)
    truth = 1.0 + 0.5 * np.sin(np.linspace(0, 12, n))
    proxy = truth * rng.chisquare(1, n)
    good = truth * 1.0
    forecasts = {
        "sgarch": good * 1.35, "egarch": good * 1.02, "gjr": good * 1.0, "figarch": good * 1.1,
        "fgarch": good * 0.98, "aparch": good * 1.01,
    }
    return {
        "dates": [str(d.date()) for d in pd.bdate_range("2023-01-02", periods=n)],
        "forecasts": {k: v.tolist() for k, v in forecasts.items()},
        "proxies": {"squared_return": proxy.tolist(), "parkinson": (proxy * 0.7).tolist(), "garman_klass": (proxy * 0.7).tolist()},
        "failures": {m: 0 for m in forecasts}, "non_converged": {m: 0 for m in forecasts},
    }


def test_evaluate_ranks_and_tests():
    out = ev.evaluate(make_payload(), proxy="parkinson")
    assert out["observations"] == 500 and out["dropped"] == 0
    assert out["scale_factor"] == pytest.approx(1 / 0.7)
    by = {m["id"]: m for m in out["models"]}
    assert out["models"][0]["rank_qlike"] == 1
    assert by["sgarch"]["rank_qlike"] == 6  # inflated forecasts are worst
    assert by["sgarch"]["dm_qlike"] is None
    assert by["gjr"]["dm_qlike"]["mean_difference"] > 0
    assert not by["sgarch"]["in_mcs_qlike"] and by["gjr"]["in_mcs_qlike"]
    assert set(out["cumulative"]["series"]) == set(by) - {"sgarch"}
    assert len(out["cumulative"]["dates"]) == 500


def test_evaluate_drops_bad_days_and_rejects_unknown_proxy():
    p = make_payload()
    p["proxies"]["parkinson"][5] = 0.0
    p["forecasts"]["egarch"][7] = float("nan")
    out = ev.evaluate(p, proxy="parkinson")
    assert out["dropped"] == 2
    with pytest.raises(ValueError):
        ev.evaluate(p, proxy="nope")
