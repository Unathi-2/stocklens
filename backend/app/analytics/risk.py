"""Risk measures: drawdown, Value at Risk, Expected Shortfall, ratios, rolling volatility, GARCH(1,1).

Pure functions on pandas Series indexed by date. No web or database code belongs here.

Conventions
- Prices are adjusted closes, so dividends are included.
- Volatility uses daily log returns, scaled by sqrt(252), as on the Performance tab.
- VaR, Expected Shortfall, Sharpe and Sortino use simple daily returns, because a loss
  is measured on the value of the position.
- Losses (VaR, ES, drawdown depth) are reported in percent. VaR and ES are positive numbers.
"""
import math
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from app.analytics.returns import TRADING_DAYS, annualised_volatility, log_returns

MIN_OBSERVATIONS = 60
GARCH_MIN_OBSERVATIONS = 500
CONFIDENCE_LEVELS = (0.95, 0.99)
ROLLING_WINDOWS = (21, 63)
BACKTEST_WINDOW = 250
BACKTEST_MIN_TESTS = 100


def _finite(x) -> float | None:
    """JSON cannot carry NaN or infinity, so unavailable values become None."""
    x = float(x)
    return x if math.isfinite(x) else None


def simple_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def drawdown_series(prices: pd.Series) -> pd.Series:
    """Percentage below the running peak. Zero at a new high, negative otherwise."""
    return (prices / prices.cummax() - 1.0) * 100.0


def drawdown_detail(prices: pd.Series) -> dict:
    """Worst drawdown with its peak, trough and recovery, plus the current state."""
    dd = prices / prices.cummax() - 1.0
    worst = float(dd.min())
    detail = {
        "max_drawdown_pct": worst * 100.0,
        "peak_date": None,
        "trough_date": None,
        "recovery_date": None,
        "current_drawdown_pct": float(dd.iloc[-1] * 100.0),
    }
    if worst < 0:
        trough = dd.idxmin()
        peak = prices.loc[:trough].idxmax()
        after = prices.loc[trough:]
        recovered = after[after >= prices.loc[peak]]
        detail["peak_date"] = peak.date()
        detail["trough_date"] = trough.date()
        detail["recovery_date"] = recovered.index[0].date() if len(recovered) else None

    # Longest run of consecutive days spent below a previous peak.
    under = dd < 0
    runs = under.groupby((~under).cumsum()).sum()
    detail["longest_underwater_days"] = int(runs.max()) if len(runs) else 0
    return detail


def value_at_risk(returns: pd.Series, confidence: float) -> dict:
    """One day VaR and Expected Shortfall at the given confidence, in percent of position value.

    historical: empirical quantile, ES is the mean of returns at or beyond it.
    normal: mean and standard deviation of the sample under normality.
    cornish_fisher: normal quantile adjusted for sample skewness and excess kurtosis.
    """
    r = returns.to_numpy()
    alpha = 1.0 - confidence
    mu, sd = r.mean(), r.std(ddof=1)
    z = stats.norm.ppf(alpha)  # negative

    q = np.quantile(r, alpha)
    tail = r[r <= q]
    s, k = stats.skew(r), stats.kurtosis(r)  # excess kurtosis
    z_cf = z + (z**2 - 1) * s / 6 + (z**3 - 3 * z) * k / 24 - (2 * z**3 - 5 * z) * s**2 / 36

    return {
        "confidence": confidence,
        "historical_var_pct": float(-q * 100.0),
        "normal_var_pct": float(-(mu + z * sd) * 100.0),
        "cornish_fisher_var_pct": float(-(mu + z_cf * sd) * 100.0),
        "historical_es_pct": float(-tail.mean() * 100.0),
        "normal_es_pct": float(-(mu - sd * stats.norm.pdf(z) / alpha) * 100.0),
    }


def kupiec_backtest(returns: pd.Series, confidence: float, window: int = BACKTEST_WINDOW) -> dict | None:
    """Out of sample check of historical VaR with the Kupiec proportion of failures test.

    Each day's VaR uses only the previous `window` returns. A violation is a return below
    that VaR. H0: the violation rate equals 1 - confidence.
    Returns None when there are too few out of sample days.
    """
    r = returns.to_numpy()
    n = len(r) - window
    if n < BACKTEST_MIN_TESTS:
        return None
    alpha = 1.0 - confidence
    windows = np.lib.stride_tricks.sliding_window_view(r, window)[:-1]
    var_q = np.quantile(windows, alpha, axis=1)
    x = int((r[window:] < var_q).sum())

    def ll(p: float) -> float:
        a = (n - x) * math.log(1 - p) if n - x > 0 else 0.0
        b = x * math.log(p) if x > 0 else 0.0
        return a + b

    lr = -2.0 * (ll(alpha) - ll(x / n))
    lr = max(lr, 0.0)
    p_value = float(stats.chi2.sf(lr, df=1))
    return {
        "confidence": confidence,
        "tests": n,
        "violations": x,
        "expected_violations": float(n * alpha),
        "violation_rate_pct": float(x / n * 100.0),
        "lr_statistic": float(lr),
        "p_value": p_value,
        "reject_null": p_value < 0.05,
    }


def ratios(prices: pd.Series, risk_free_pct: float = 0.0) -> dict:
    """Return per unit of risk. risk_free_pct is an annual rate in percent."""
    r = simple_returns(prices)
    lr = log_returns(prices)
    years = (prices.index[-1] - prices.index[0]).days / 365.25
    total = prices.iloc[-1] / prices.iloc[0]
    cagr = total ** (1.0 / years) - 1.0 if years > 0 else float("nan")

    rf_daily = (1.0 + risk_free_pct / 100.0) ** (1.0 / TRADING_DAYS) - 1.0
    excess = r - rf_daily
    sd = r.std(ddof=1)
    downside = math.sqrt(float(np.mean(np.minimum(excess, 0.0) ** 2)))
    max_dd = float((prices / prices.cummax() - 1.0).min())

    sharpe = excess.mean() / sd * math.sqrt(TRADING_DAYS) if sd > 0 else float("nan")
    sortino = excess.mean() / downside * math.sqrt(TRADING_DAYS) if downside > 0 else float("nan")
    calmar = cagr / abs(max_dd) if max_dd < 0 else float("nan")

    return {
        "annualised_return_pct": _finite(cagr * 100.0),
        "annualised_volatility_pct": float(annualised_volatility(lr) * 100.0),
        "downside_deviation_pct": float(downside * math.sqrt(TRADING_DAYS) * 100.0),
        "sharpe": _finite(sharpe),
        "sortino": _finite(sortino),
        "calmar": _finite(calmar),
        "risk_free_pct": float(risk_free_pct),
    }


def rolling_volatility(prices: pd.Series, window: int) -> pd.Series:
    """Annualised volatility in percent over a rolling window of daily log returns."""
    r = log_returns(prices)
    return (r.rolling(window).std(ddof=1) * math.sqrt(TRADING_DAYS) * 100.0).dropna()


def garch11(returns_pct: pd.Series) -> dict | None:
    """GARCH(1,1) with a constant mean and normal errors, fitted by maximum likelihood.

    sigma2_t = omega + alpha * e2_{t-1} + beta * sigma2_{t-1}
    Returns None when the sample is too short or the fit fails.
    """
    if len(returns_pct) < GARCH_MIN_OBSERVATIONS:
        return None
    from arch import arch_model

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = arch_model(returns_pct, mean="Constant", vol="GARCH", p=1, q=1, dist="normal", rescale=False).fit(
                disp="off", show_warning=False
            )
    except Exception:  # noqa: BLE001 - a failed optimiser must not break the whole risk response
        return None

    p = res.params
    omega, alpha, beta = float(p["omega"]), float(p["alpha[1]"]), float(p["beta[1]"])
    persistence = alpha + beta
    stationary = persistence < 1.0
    cond = res.conditional_volatility * math.sqrt(TRADING_DAYS)

    return {
        "converged": bool(res.convergence_flag == 0),
        "parameters": [
            {
                "name": name,
                "estimate": float(p[key]),
                "std_error": _finite(res.std_err[key]),
                "p_value": _finite(res.pvalues[key]),
            }
            for name, key in (("mu", "mu"), ("omega", "omega"), ("alpha", "alpha[1]"), ("beta", "beta[1]"))
        ],
        "persistence": float(persistence),
        "half_life_days": _finite(math.log(0.5) / math.log(persistence)) if 0 < persistence < 1 else None,
        "unconditional_volatility_pct": _finite(math.sqrt(omega / (1 - persistence) * TRADING_DAYS))
        if stationary
        else None,
        "latest_volatility_pct": float(cond.iloc[-1]),
        "log_likelihood": float(res.loglikelihood),
        "aic": float(res.aic),
        "bic": float(res.bic),
        "observations": int(len(returns_pct)),
        "volatility": cond,
    }


def analyse(prices: pd.Series, risk_free_pct: float = 0.0) -> dict:
    """Everything the Risk tab shows. Needs at least MIN_OBSERVATIONS + 1 prices."""
    r = simple_returns(prices)
    lr_pct = log_returns(prices) * 100.0
    return {
        "summary": ratios(prices, risk_free_pct),
        "drawdown": {**drawdown_detail(prices), "series": drawdown_series(prices)},
        "rolling_volatility": {w: rolling_volatility(prices, w) for w in ROLLING_WINDOWS},
        "var": [value_at_risk(r, c) for c in CONFIDENCE_LEVELS],
        "backtests": [b for c in CONFIDENCE_LEVELS if (b := kupiec_backtest(r, c)) is not None],
        "garch": garch11(lr_pct),
    }
