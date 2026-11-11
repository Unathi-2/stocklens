import math
import warnings

import numpy as np
import pandas as pd
import pytest

from app.analytics import volatility as v
from test_risk import prices_from_log_returns


def gjr_returns(n=1200, seed=5, omega=0.04, alpha=0.04, gamma=0.14, beta=0.88):
    rng = np.random.default_rng(seed)
    r, var = np.zeros(n), omega / (1 - alpha - gamma / 2 - beta)
    for t in range(n):
        r[t] = np.sqrt(var) * rng.standard_normal()
        var = omega + (alpha + (gamma if r[t] < 0 else 0.0)) * r[t] ** 2 + beta * var
    return r


@pytest.fixture(scope="module")
def fitted():
    return v.analyse(prices_from_log_returns(gjr_returns()))


def by_id(result):
    return {m["id"]: m for m in result["models"]}


def test_persistence_special_cases():
    assert v.persistence("sgarch", {"alpha": 0.1, "beta": 0.85}) == pytest.approx(0.95)
    assert v.persistence("gjr", {"alpha": 0.04, "gamma": 0.1, "beta": 0.9}) == pytest.approx(0.99)
    assert v.persistence("egarch", {"beta": 0.97}) == 0.97
    # with no asymmetry and delta 2, APARCH and fGARCH both collapse to alpha + beta
    assert v.persistence("aparch", {"alpha": 0.1, "beta": 0.85, "gamma": 0.0, "delta": 2.0}) == pytest.approx(0.95, abs=1e-6)
    assert v.persistence(
        "fgarch", {"alpha": 0.1, "beta": 0.85, "eta1": 0.0, "eta2": 0.0, "delta": 2.0}
    ) == pytest.approx(0.95, abs=1e-6)
    assert v.persistence("figarch", {}) is None


def test_all_six_models_fit_in_order(fitted):
    assert [m["id"] for m in fitted["models"]] == ["sgarch", "egarch", "gjr", "figarch", "fgarch", "aparch"]
    for m in fitted["models"]:
        assert m["converged"] and m["error"] is None
        assert len(m["volatility"]) == fitted["observations"] == len(fitted["dates"]) == len(fitted["realised_21d"])
        assert len(m["forecast"]) == v.HORIZON and all(x > 0 and math.isfinite(x) for x in m["forecast"])
        assert m["aic"] == pytest.approx(-2 * m["log_likelihood"] + 2 * m["n_params"])
        assert m["bic"] > m["aic"]
        assert 0 <= m["residual_tests"]["ljung_box_squared_p"] <= 1
    assert len(fitted["forecast_dates"]) == v.HORIZON


def test_asymmetric_models_win_on_leverage_data(fitted):
    m = by_id(fitted)
    assert fitted["best_aic"] in {"gjr", "aparch", "fgarch", "egarch"}
    assert m["sgarch"]["aic"] - m["gjr"]["aic"] > 5
    gamma = {p["name"]: p["estimate"] for p in m["gjr"]["parameters"]}["gamma"]
    assert gamma == pytest.approx(0.14, abs=0.09)
    # in the arch EGARCH form a negative gamma means bad news raises volatility more than good news
    assert {p["name"]: p["estimate"] for p in m["egarch"]["parameters"]}["gamma"] < 0


def test_fgarch_is_at_least_as_good_as_aparch(fitted):
    m = by_id(fitted)
    assert m["fgarch"]["log_likelihood"] >= m["aparch"]["log_likelihood"] - 0.5


def test_news_impact_curves(fitted):
    m = by_id(fitted)
    assert m["figarch"]["news_impact"] is None
    gjr = m["gjr"]["news_impact"]
    shock, vol = gjr["shock"], gjr["volatility"]
    assert vol[shock.index(-3.0)] > vol[shock.index(3.0)]  # leverage effect
    sg = m["sgarch"]["news_impact"]["volatility"]
    assert sg[10] == pytest.approx(sg[30], rel=1e-9)  # symmetric
    assert min(sg) == sg[20]  # lowest at no shock


def test_news_impact_matches_one_step_forecasts():
    """next_volatility must reproduce what each fitted model forecasts for tomorrow."""
    from arch import arch_model

    r = pd.Series(gjr_returns(900)) 
    for model_id in ("sgarch", "gjr", "egarch", "aparch"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = arch_model(r, mean="Constant", dist="normal", rescale=False, **v.ARCH_SPECS[model_id]).fit(disp="off", show_warning=False)
        p = {v.ARCH_KEYS[k]: float(x) for k, x in res.params.items()}
        sigma = float(res.conditional_volatility.iloc[-1])
        z = float(res.std_resid.iloc[-1])
        expected = math.sqrt(float(res.forecast(horizon=1).variance.iloc[-1].iloc[0]))
        assert v.next_volatility(model_id, p, sigma, z) == pytest.approx(expected, rel=1e-4), model_id


def test_fgarch_news_impact_matches_its_filter():
    r = pd.Series(gjr_returns(900))
    fit = v.fit_fgarch(r)
    theta = fit["theta"]
    sig, eps, h_next = v._fgarch_filter(theta, r.to_numpy())
    p = dict(zip(v._FG_NAMES, theta))
    got = v.next_volatility("fgarch", p, float(sig[-1]), float(eps[-1] / sig[-1]))
    assert got == pytest.approx(h_next ** (1 / p["delta"]), rel=1e-9)


def test_fgarch_recovers_a_garch_process():
    """Fitted to plain GARCH data, fGARCH should not find a large asymmetry."""
    rng = np.random.default_rng(8)
    n, r, var = 1500, np.zeros(1500), 1.0
    for t in range(n):
        r[t] = math.sqrt(var) * rng.standard_normal()
        var = 0.05 + 0.08 * r[t] ** 2 + 0.88 * var
    fit = v.fit_fgarch(pd.Series(r))
    p = dict(zip(v._FG_NAMES, fit["theta"]))
    assert v.persistence("fgarch", p) == pytest.approx(0.96, abs=0.05)


def test_needs_enough_history():
    with pytest.raises(ValueError):
        v.analyse(prices_from_log_returns(gjr_returns(300)))
