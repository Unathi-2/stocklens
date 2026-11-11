"""Volatility models and their comparison: sGARCH, EGARCH, GJR-GARCH, FIGARCH, fGARCH and APARCH.

Pure functions on a pandas Series of prices. No web or database code belongs here.

All models use daily log returns in percent, a constant mean and normal errors, and are
estimated by (quasi) maximum likelihood. Five come from the `arch` package. fGARCH, the
family GARCH of Hentschel (1995), is not in `arch`, so it is estimated here:

    sigma_t^d = omega + alpha * sigma_{t-1}^d * (|z_{t-1} - eta2| - eta1 * (z_{t-1} - eta2))^d + beta * sigma_{t-1}^d

with z = e / sigma. This is the "ALLGARCH" submodel of the family (lambda equal to delta). It contains
APARCH (eta2 = 0), GJR-like asymmetry (eta1) and a shifted news impact curve (eta2).
"""
import math
import warnings

import numpy as np
import pandas as pd
from scipy import integrate, optimize, stats
from statsmodels.stats.diagnostic import acorr_ljungbox

from app.analytics.returns import TRADING_DAYS, log_returns

MIN_OBSERVATIONS = 500
HORIZON = 10
FORECAST_SIMULATIONS = 5000
SEED = 20240611
LJUNG_BOX_LAGS = 10

MODELS: list[tuple[str, str]] = [
    ("sgarch", "sGARCH(1,1)"),
    ("egarch", "EGARCH(1,1)"),
    ("gjr", "GJR-GARCH(1,1)"),
    ("figarch", "FIGARCH(1,d,1)"),
    ("fgarch", "fGARCH(1,1)"),
    ("aparch", "APARCH(1,1)"),
]
NAMES = dict(MODELS)

ARCH_SPECS = {
    "sgarch": dict(vol="GARCH", p=1, q=1),
    "egarch": dict(vol="EGARCH", p=1, o=1, q=1),
    "gjr": dict(vol="GARCH", p=1, o=1, q=1),
    "figarch": dict(vol="FIGARCH", p=1, q=1),
    "aparch": dict(vol="APARCH", p=1, o=1, q=1),
}
ARCH_KEYS = {
    "mu": "mu", "omega": "omega", "alpha[1]": "alpha", "gamma[1]": "gamma", "beta[1]": "beta",
    "beta": "beta", "phi": "phi", "d": "d", "delta": "delta",
}
PARAM_ORDER = ["mu", "omega", "alpha", "gamma", "beta", "phi", "d", "delta", "eta1", "eta2"]
SQRT_252 = math.sqrt(TRADING_DAYS)


def _finite(x) -> float | None:
    x = float(x)
    return x if math.isfinite(x) else None


# ---------------------------------------------------------------- shared formulas


def _expect_normal(f) -> float:
    """E[f(z)] for a standard normal z."""
    value, _ = integrate.quad(lambda z: f(z) * stats.norm.pdf(z), -12.0, 12.0, limit=200)
    return float(value)


def persistence(model_id: str, p: dict[str, float]) -> float | None:
    """Rate at which the variance process forgets a shock. None for FIGARCH, which has hyperbolic memory."""
    if model_id == "sgarch":
        return p["alpha"] + p["beta"]
    if model_id == "gjr":
        return p["alpha"] + p["gamma"] / 2.0 + p["beta"]
    if model_id == "egarch":
        return p["beta"]
    if model_id == "aparch":
        d, g = p["delta"], p["gamma"]
        return p["beta"] + p["alpha"] * _expect_normal(lambda z: (abs(z) - g * z) ** d)
    if model_id == "fgarch":
        d, e1, e2 = p["delta"], p["eta1"], p["eta2"]
        return p["beta"] + p["alpha"] * _expect_normal(lambda z: (abs(z - e2) - e1 * (z - e2)) ** d)
    return None


def next_volatility(model_id: str, p: dict[str, float], sigma: float, z: float) -> float | None:
    """One step ahead conditional volatility (daily, percent) after a shock of z standard deviations,
    when the current conditional volatility is `sigma`. None for FIGARCH (no one term news impact)."""
    e = z * sigma
    if model_id == "sgarch":
        return math.sqrt(p["omega"] + p["alpha"] * e**2 + p["beta"] * sigma**2)
    if model_id == "gjr":
        return math.sqrt(p["omega"] + (p["alpha"] + (p["gamma"] if e < 0 else 0.0)) * e**2 + p["beta"] * sigma**2)
    if model_id == "egarch":
        log_var = p["omega"] + p["alpha"] * (abs(z) - math.sqrt(2 / math.pi)) + p["gamma"] * z + p["beta"] * math.log(sigma**2)
        return math.sqrt(math.exp(log_var))
    if model_id == "aparch":
        d = p["delta"]
        h = p["omega"] + p["alpha"] * (abs(e) - p["gamma"] * e) ** d + p["beta"] * sigma**d
        return h ** (1.0 / d)
    if model_id == "fgarch":
        d, x = p["delta"], z - p["eta2"]
        f = abs(x) - p["eta1"] * x
        h = p["omega"] + p["alpha"] * sigma**d * f**d + p["beta"] * sigma**d
        return h ** (1.0 / d)
    return None


def news_impact(model_id: str, p: dict[str, float], sigma: float) -> dict | None:
    """Next day volatility (annualised percent) for shocks from -4 to +4 standard deviations."""
    grid = np.linspace(-4.0, 4.0, 41)
    values = [next_volatility(model_id, p, sigma, float(z)) for z in grid]
    if any(v is None or not math.isfinite(v) for v in values):
        return None
    return {"shock": [float(z) for z in grid], "volatility": [float(v * SQRT_252) for v in values]}


def _residual_tests(z: np.ndarray) -> dict:
    z = z[np.isfinite(z)]
    lb = acorr_ljungbox(z, lags=[LJUNG_BOX_LAGS], return_df=True)["lb_pvalue"].iloc[0]
    lb2 = acorr_ljungbox(z**2, lags=[LJUNG_BOX_LAGS], return_df=True)["lb_pvalue"].iloc[0]
    return {
        "ljung_box_p": float(lb),
        "ljung_box_squared_p": float(lb2),
        "jarque_bera_p": float(stats.jarque_bera(z).pvalue),
    }


# ---------------------------------------------------------------- fGARCH estimation

_FG_NAMES = ["mu", "omega", "alpha", "beta", "eta1", "eta2", "delta"]
_FG_BOUNDS = [(-2.0, 2.0), (1e-8, 50.0), (0.0, 1.0), (0.0, 0.9999), (-0.99, 0.99), (-2.0, 2.0), (0.5, 3.5)]


def _fgarch_filter(theta, r: np.ndarray):
    # plain Python floats: overflow raises OverflowError (handled) instead of a numpy warning
    mu, omega, alpha, beta, eta1, eta2, delta = (float(t) for t in theta)
    inv = 1.0 / delta
    eps = (r - mu).tolist()
    h = (sum(e * e for e in eps) / len(eps)) ** (delta / 2.0)
    sig = [0.0] * len(eps)
    for t, e in enumerate(eps):
        s = h**inv
        sig[t] = s
        x = e / s - eta2
        f = abs(x) - eta1 * x
        h = omega + (alpha * f**delta + beta) * h
    return np.array(sig), np.array(eps), h


def _fgarch_nll(theta, r: np.ndarray) -> float:
    try:
        sig, eps, _ = _fgarch_filter(theta, r)
    except (OverflowError, ZeroDivisionError, ValueError):
        return 1e10
    if not np.all(np.isfinite(sig)) or np.any(sig <= 0):
        return 1e10
    return float(0.5 * np.sum(math.log(2 * math.pi) + 2 * np.log(sig) + (eps / sig) ** 2))


def _hessian(f, x: np.ndarray) -> np.ndarray:
    n = len(x)
    step = 1e-3 * np.maximum(np.abs(x), 0.05)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            ei, ej = np.zeros(n), np.zeros(n)
            ei[i], ej[j] = step[i], step[j]
            H[i, j] = H[j, i] = (f(x + ei + ej) - f(x + ei - ej) - f(x - ei + ej) + f(x - ei - ej)) / (4 * step[i] * step[j])
    return H


def fit_fgarch(r: pd.Series, start_hint: dict[str, float] | None = None) -> dict:
    """Quasi maximum likelihood for fGARCH(1,1). Starts from a GARCH like point and, when given, from an APARCH fit."""
    x = r.to_numpy(dtype=float)
    var0 = float(np.var(x))
    mu0 = float(np.mean(x))
    starts = [[mu0, 0.05 * var0, 0.10, 0.85, 0.0, 0.0, 2.0]]
    if start_hint:
        starts.append([
            start_hint["mu"], start_hint["omega"], start_hint["alpha"], start_hint["beta"],
            start_hint.get("gamma", 0.0), 0.0, start_hint["delta"],
        ])
    best = None
    for s in starts:
        s = [min(max(v, lo), hi) for v, (lo, hi) in zip(s, _FG_BOUNDS)]
        res = optimize.minimize(_fgarch_nll, s, args=(x,), method="L-BFGS-B", bounds=_FG_BOUNDS, options={"maxiter": 400})
        if best is None or res.fun < best.fun:
            best = res
    theta = best.x
    nll = _fgarch_nll(theta, x)
    if nll >= 1e9:
        raise RuntimeError("fGARCH likelihood could not be evaluated")

    se = [None] * len(theta)
    try:
        H = _hessian(lambda t: _fgarch_nll(t, x), theta)
        if np.all(np.isfinite(H)) and np.linalg.eigvalsh(H).min() > 0:
            diag = np.sqrt(np.diag(np.linalg.inv(H)))
            for i, ((lo, hi), v) in enumerate(zip(_FG_BOUNDS, theta)):
                at_bound = abs(v - lo) < 1e-6 or abs(v - hi) < 1e-6
                se[i] = None if at_bound else _finite(diag[i])
    except np.linalg.LinAlgError:
        pass
    return {"theta": theta, "log_likelihood": -nll, "converged": bool(best.success), "std_errors": se}


def _fgarch_forecast(theta, h_next: float, horizon: int) -> np.ndarray:
    _, omega, alpha, beta, eta1, eta2, delta = theta
    rng = np.random.default_rng(SEED)
    h = np.full(FORECAST_SIMULATIONS, h_next)
    out = np.empty(horizon)
    for k in range(horizon):
        out[k] = np.mean(h ** (2.0 / delta))
        x = rng.standard_normal(FORECAST_SIMULATIONS) - eta2
        f = np.abs(x) - eta1 * x
        h = omega + (alpha * f**delta + beta) * h
    return out


# ---------------------------------------------------------------- packaging


def _package(model_id, params, std_errors, p_values, loglik, n_obs, converged, cond_vol, std_resid, forecast_var, memory_d=None):
    n_params = len(params)
    p = dict(params)
    pers = persistence(model_id, p)
    if pers is not None and not math.isfinite(pers):
        pers = None
    sigma_bar = float(np.mean(cond_vol))
    return {
        "id": model_id,
        "name": NAMES[model_id],
        "converged": converged,
        "error": None,
        "n_params": n_params,
        "log_likelihood": float(loglik),
        "aic": float(-2 * loglik + 2 * n_params),
        "bic": float(-2 * loglik + n_params * math.log(n_obs)),
        "parameters": [
            {"name": k, "estimate": float(params[k]), "std_error": std_errors.get(k), "p_value": p_values.get(k)}
            for k in PARAM_ORDER if k in params
        ],
        "persistence": pers,
        "half_life_days": _finite(math.log(0.5) / math.log(pers)) if pers is not None and 0 < pers < 1 else None,
        "memory_d": memory_d,
        "mean_volatility_pct": float(sigma_bar * SQRT_252),
        "latest_volatility_pct": float(cond_vol[-1] * SQRT_252),
        "residual_tests": _residual_tests(std_resid),
        "volatility": [round(float(v * SQRT_252), 3) for v in cond_vol],
        "forecast": [float(math.sqrt(v) * SQRT_252) for v in forecast_var],
        "news_impact": news_impact(model_id, p, sigma_bar),
    }


def _failed(model_id: str, message: str) -> dict:
    return {
        "id": model_id, "name": NAMES[model_id], "converged": False, "error": message, "n_params": None,
        "log_likelihood": None, "aic": None, "bic": None, "parameters": [], "persistence": None,
        "half_life_days": None, "memory_d": None, "mean_volatility_pct": None, "latest_volatility_pct": None,
        "residual_tests": None, "volatility": [], "forecast": [], "news_impact": None,
    }


def _arch_forecast(res, model_id: str) -> np.ndarray:
    if model_id in {"sgarch", "gjr", "figarch"}:
        try:
            return res.forecast(horizon=HORIZON, method="analytic").variance.iloc[-1].to_numpy()
        except Exception:  # noqa: BLE001 - fall back to simulation
            pass
    return res.forecast(
        horizon=HORIZON, method="simulation", simulations=FORECAST_SIMULATIONS,
        random_state=np.random.RandomState(SEED),
    ).variance.iloc[-1].to_numpy()


def fit_arch_model(model_id: str, r: pd.Series) -> dict:
    from arch import arch_model

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = arch_model(r, mean="Constant", dist="normal", rescale=False, **ARCH_SPECS[model_id]).fit(
            disp="off", show_warning=False
        )
        forecast_var = _arch_forecast(res, model_id)
    params = {ARCH_KEYS[k]: float(v) for k, v in res.params.items()}
    se = {ARCH_KEYS[k]: _finite(v) for k, v in res.std_err.items()}
    pv = {ARCH_KEYS[k]: _finite(v) for k, v in res.pvalues.items()}
    z = res.std_resid.to_numpy()
    out = _package(
        model_id, params, se, pv, res.loglikelihood, len(r), bool(res.convergence_flag == 0),
        res.conditional_volatility.to_numpy(), z, forecast_var, memory_d=params.get("d"),
    )
    out["_params"] = params
    return out


def fit_fgarch_model(r: pd.Series, hint: dict[str, float] | None) -> dict:
    fit = fit_fgarch(r, hint)
    theta = fit["theta"]
    params = dict(zip(_FG_NAMES, (float(v) for v in theta)))
    se = dict(zip(_FG_NAMES, fit["std_errors"]))
    pv = {k: (_finite(2 * stats.norm.sf(abs(params[k] / s))) if s else None) for k, s in se.items()}
    sig, eps, h_next = _fgarch_filter(theta, r.to_numpy(dtype=float))
    forecast_var = _fgarch_forecast(theta, h_next, HORIZON)
    out = _package(
        "fgarch", params, se, pv, fit["log_likelihood"], len(r), fit["converged"], sig, eps / sig, forecast_var
    )
    out["_params"] = params
    return out


def analyse(prices: pd.Series) -> dict:
    """Fit all six models to the window and compare them. Needs MIN_OBSERVATIONS returns."""
    lr = log_returns(prices) * 100.0
    if len(lr) < MIN_OBSERVATIONS:
        raise ValueError("not enough observations")

    results: dict[str, dict] = {}
    for model_id, _ in MODELS:
        try:
            if model_id == "fgarch":
                a = results.get("aparch")
                hint = a["_params"] if a and a.get("converged") else None
                results[model_id] = fit_fgarch_model(lr, hint)
            else:
                results[model_id] = fit_arch_model(model_id, lr)
        except Exception as exc:  # noqa: BLE001 - one failing model must not break the comparison
            results[model_id] = _failed(model_id, f"{type(exc).__name__}: {str(exc)[:120]}")

    models = [results[m] for m, _ in MODELS]
    for m in models:
        m.pop("_params", None)
    ok = [m for m in models if m["converged"] and m["aic"] is not None]
    realised = (lr.rolling(21).std(ddof=1) * SQRT_252).to_numpy()

    return {
        "dates": [ts.date() for ts in lr.index],
        "observations": int(len(lr)),
        "horizon": HORIZON,
        "forecast_dates": [d.date() for d in pd.bdate_range(prices.index[-1] + pd.Timedelta(days=1), periods=HORIZON)],
        "realised_21d": [round(float(v), 3) if math.isfinite(v) else None for v in realised],
        "models": models,
        "best_aic": min(ok, key=lambda m: m["aic"])["id"] if ok else None,
        "best_bic": min(ok, key=lambda m: m["bic"])["id"] if ok else None,
    }
