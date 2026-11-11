"""Distribution and time series diagnostics for a price window.

Pure functions, no web or database code. Everything is computed on daily log
returns in percent. Tests report the statistic, the p value and a plain reading
of the evidence at the 5% level. They never say pass or fail.
"""
import warnings
from contextlib import contextmanager

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.tsa.stattools import acf, adfuller, pacf

from app.analytics.returns import log_returns

ALPHA = 0.05
MIN_OBSERVATIONS = 60


@contextmanager
def _quiet():
    """statsmodels announces future return type changes. They do not affect these results."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        yield


def _result(
    test_id: str,
    name: str,
    applied_to: str,
    null: str,
    statistic: float,
    p_value: float,
    if_rejected: str,
    if_not_rejected: str,
    details: dict,
) -> dict:
    reject = bool(p_value < ALPHA)
    p_text = "p < 0.0001" if p_value < 0.0001 else f"p = {p_value:.4f}"
    lead = "Evidence against the null hypothesis at the 5% level" if reject else "Insufficient evidence to reject the null hypothesis at the 5% level"
    return {
        "id": test_id,
        "name": name,
        "applied_to": applied_to,
        "null_hypothesis": null,
        "statistic": float(statistic),
        "p_value": float(p_value),
        "reject_null": reject,
        "alpha": ALPHA,
        "interpretation": f"{lead} ({p_text}). {if_rejected if reject else if_not_rejected}",
        "details": details,
    }


def adf_test(series: np.ndarray, test_id: str, applied_to: str) -> dict:
    """Augmented Dickey Fuller test with a constant and AIC lag selection."""
    with _quiet():
        stat, p, used_lag, nobs, crit, _ = adfuller(series, autolag="AIC")
    return _result(
        test_id, "Augmented Dickey Fuller", applied_to,
        "The series has a unit root (it is not stationary).",
        stat, p,
        "The series looks stationary.",
        "The data are consistent with a non stationary series.",
        {
            "lags_used": int(used_lag),
            "observations": int(nobs),
            "critical_value_1pct": float(crit["1%"]),
            "critical_value_5pct": float(crit["5%"]),
            "critical_value_10pct": float(crit["10%"]),
        },
    )


def arch_lm_test(x: np.ndarray, lags: int = 5) -> dict:
    """Engle's ARCH LM test on demeaned returns."""
    with _quiet():
        lm, lm_p, f, f_p = het_arch(x - x.mean(), nlags=lags)
    return _result(
        "arch_lm", "ARCH LM", "Daily log returns",
        f"There are no ARCH effects: the variance of returns does not depend on past squared returns (tested with {lags} lags).",
        lm, lm_p,
        "Volatility clusters over time, so a conditional volatility model such as GARCH is worth fitting.",
        "No clear volatility clustering was found in this window.",
        {"lags": lags, "f_statistic": float(f), "f_p_value": float(f_p)},
    )


def jarque_bera_test(x: np.ndarray) -> dict:
    res = stats.jarque_bera(x)
    return _result(
        "jarque_bera", "Jarque Bera", "Daily log returns",
        "Returns are normally distributed (skewness 0 and excess kurtosis 0).",
        res.statistic, res.pvalue,
        "Returns are not normal, which is usual for fat tailed financial returns.",
        "Normality is not rejected in this window.",
        {"skewness": float(stats.skew(x)), "excess_kurtosis": float(stats.kurtosis(x))},
    )


def ljung_box_test(x: np.ndarray, lags: int, test_id: str, applied_to: str, if_rejected: str, if_not_rejected: str) -> dict:
    with _quiet():
        lb = acorr_ljungbox(x, lags=[lags], return_df=True)
    return _result(
        test_id, "Ljung Box", applied_to,
        f"There is no autocorrelation up to lag {lags}.",
        lb["lb_stat"].iloc[0], lb["lb_pvalue"].iloc[0],
        if_rejected, if_not_rejected,
        {"lags": lags},
    )


def summary_stats(x: np.ndarray) -> dict:
    return {
        "observations": int(len(x)),
        "mean_pct": float(x.mean()),
        "median_pct": float(np.median(x)),
        "std_pct": float(x.std(ddof=1)),
        "skewness": float(stats.skew(x)),
        "excess_kurtosis": float(stats.kurtosis(x)),
        "min_pct": float(x.min()),
        "max_pct": float(x.max()),
    }


def histogram(x: np.ndarray, bins: int = 40) -> dict:
    density, edges = np.histogram(x, bins=bins, density=True)
    centers = (edges[:-1] + edges[1:]) / 2
    normal = stats.norm.pdf(centers, loc=x.mean(), scale=x.std(ddof=1))
    return {
        "bin_centers": centers.round(5).tolist(),
        "density": density.round(6).tolist(),
        "normal_density": normal.round(6).tolist(),
        "bin_width": float(edges[1] - edges[0]),
    }


def qq(x: np.ndarray) -> dict:
    """Standardised sample quantiles against standard normal quantiles."""
    n = len(x)
    probs = (np.arange(1, n + 1) - 0.5) / n
    theoretical = stats.norm.ppf(probs)
    sample = np.sort((x - x.mean()) / x.std(ddof=1))
    return {"theoretical": theoretical.round(4).tolist(), "sample": sample.round(4).tolist()}


def correlograms(x: np.ndarray, max_lags: int = 30) -> dict:
    n = len(x)
    lags = int(min(max_lags, n // 2 - 1))
    return {
        "lags": list(range(1, lags + 1)),
        "returns": acf(x, nlags=lags, fft=True)[1:].round(5).tolist(),
        "squared_returns": acf(x**2, nlags=lags, fft=True)[1:].round(5).tolist(),
        "pacf_returns": pacf(x, nlags=lags, method="ywm")[1:].round(5).tolist(),
        "confidence_bound": float(1.96 / np.sqrt(n)),
    }


def analyse(prices: pd.Series, lb_lags: int = 10, arch_lags: int = 5) -> dict:
    """Full statistical profile of a price window. Needs MIN_OBSERVATIONS returns."""
    x = (log_returns(prices) * 100.0).to_numpy()
    log_price = np.log(prices.to_numpy())

    tests = [
        adf_test(log_price, "adf_log_price", "Log prices"),
        adf_test(x, "adf_returns", "Daily log returns"),
        arch_lm_test(x, arch_lags),
        jarque_bera_test(x),
        ljung_box_test(
            x, lb_lags, "ljung_box_returns", "Daily log returns",
            "Returns are autocorrelated, so past returns carry some information about later ones.",
            "No clear autocorrelation in returns, as expected in an efficient market.",
        ),
        ljung_box_test(
            x**2, lb_lags, "ljung_box_squared", "Squared daily log returns",
            "Squared returns are autocorrelated, which is the signature of volatility clustering.",
            "No clear autocorrelation in squared returns.",
        ),
    ]
    return {
        "summary": summary_stats(x),
        "histogram": histogram(x),
        "qq": qq(x),
        "tests": tests,
        "acf": correlograms(x),
    }
