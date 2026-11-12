"""Out of sample evaluation of volatility forecasts.

Pure functions. No web or database code belongs here.

Scheme
- Every `refit_every` trading days each model is re-estimated on the previous `window` returns.
- Its parameters are then held fixed while the variance recursion runs forward over the next block, so
  each one day ahead forecast for day t uses only returns up to t-1 and parameters estimated before t.
- Forecasts are compared with a realised variance proxy for the same day.

Losses (h is the forecast, p the proxy, both daily variance in percent squared)
- QLIKE = p/h - ln(p/h) - 1. Zero when p equals h. Under forecasting too low it grows faster than too high.
- MSE = (p - h)^2.
Both are robust to noise in the proxy in the sense of Patton (2011), provided the proxy is unbiased.

Inference
- Diebold Mariano test of equal expected loss against a benchmark, Newey West variance and the
  Harvey, Leybourne and Newbold small sample correction.
- Model Confidence Set of Hansen, Lunde and Nason (2011), range statistic T_max, circular block bootstrap.
"""
import math

import numpy as np
import pandas as pd
from scipy import stats

from app.analytics import volatility as vol

LN2 = math.log(2.0)
PROXIES = ("parkinson", "garman_klass", "squared_return")
MCS_ALPHA = 0.10
BOOTSTRAP_DRAWS = 1000
SEED = 20241111
MODEL_ORDER = [m for m, _ in vol.MODELS]
FIT_ORDER = ["sgarch", "egarch", "gjr", "figarch", "aparch", "fgarch"]  # aparch before fgarch: it seeds fgarch


# ---------------------------------------------------------------- proxies


def variance_proxies(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Daily variance proxies in percent squared, indexed by date and aligned with log returns of the adjusted close.

    df needs columns open, high, low, close and adjusted_close, in date order.
    - squared_return: squared close to close log return of the adjusted close.
    - parkinson: ln(H/L)^2 / (4 ln 2). Uses the high low range only.
    - garman_klass: 0.5 ln(H/L)^2 - (2 ln 2 - 1) ln(C/O)^2.
    The range proxies ignore the overnight gap, so they are rescaled to the mean of the squared returns when evaluated.
    """
    adj = df["adjusted_close"].astype(float)
    r = np.log(adj / adj.shift(1)) * 100.0
    hl = (np.log(df["high"].astype(float) / df["low"].astype(float)) * 100.0) ** 2
    co = (np.log(df["close"].astype(float) / df["open"].astype(float)) * 100.0) ** 2
    out = {
        "squared_return": r**2,
        "parkinson": hl / (4.0 * LN2),
        "garman_klass": 0.5 * hl - (2.0 * LN2 - 1.0) * co,
    }
    return {k: v.iloc[1:] for k, v in out.items()}


# ---------------------------------------------------------------- rolling forecasts


def _fit_window(model_id: str, win: pd.Series, hint: dict | None):
    """Estimate one model on a window. Returns (params for fixing, converged)."""
    from arch import arch_model

    if model_id == "fgarch":
        fit = vol.fit_fgarch(win, hint)
        return fit["theta"], bool(fit["converged"])
    res = arch_model(win, mean="Constant", dist="normal", rescale=False, **vol.ARCH_SPECS[model_id]).fit(
        disp="off", show_warning=False
    )
    return res.params, bool(res.convergence_flag == 0)


def _block_variance(model_id: str, params, r: pd.Series, s: int, e: int, init_var: float) -> np.ndarray:
    """One step ahead variance for observations s..e-1 with parameters held fixed.

    The model only sees returns up to e. For FIGARCH, arch sets the pre sample variance from the series it is
    given, so forecasts in a block carry a negligible (below 0.05 percent) dependence on that block's own returns.
    """
    from arch import arch_model

    if model_id == "fgarch":
        sig, _, _ = vol._fgarch_filter(params, r.to_numpy(dtype=float)[:e], init_var=init_var)
        return sig[s:e] ** 2
    model = arch_model(r.iloc[:e], mean="Constant", dist="normal", rescale=False, **vol.ARCH_SPECS[model_id])
    return model.fix(params).conditional_volatility.to_numpy()[s:e] ** 2


def rolling_forecasts(r: pd.Series, window: int = 500, refit_every: int = 20, progress=None) -> dict:
    """Rolling one day ahead variance forecasts for the six models.

    r: daily log returns in percent. Forecasts exist for observations window .. len(r)-1.
    """
    import warnings

    n = len(r)
    if n < window + refit_every:
        raise ValueError("not enough returns for the chosen window")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        forecasts = {m: np.full(n, np.nan) for m in MODEL_ORDER}
        failures = {m: 0 for m in MODEL_ORDER}
        non_converged = {m: 0 for m in MODEL_ORDER}
        last_params: dict = {}
        starts = list(range(window, n, refit_every))

        for k, s in enumerate(starts):
            e = min(s + refit_every, n)
            win = r.iloc[s - window : s]
            init_var = float(np.mean((win.to_numpy() - win.mean()) ** 2))
            hint = None
            for m in FIT_ORDER:
                try:
                    params, ok = _fit_window(m, win, hint if m == "fgarch" else None)
                    h = _block_variance(m, params, r, s, e, init_var)
                    if not (np.all(np.isfinite(h)) and np.all(h > 0)):
                        raise FloatingPointError("invalid variance forecast")
                    last_params[m] = params
                    if not ok:
                        non_converged[m] += 1
                    if m == "aparch":
                        p = {vol.ARCH_KEYS[a]: float(b) for a, b in params.items()}
                        hint = {"mu": p["mu"], "omega": p["omega"], "alpha": p["alpha"], "beta": p["beta"],
                                "gamma": p["gamma"], "delta": p["delta"]}
                except Exception:  # noqa: BLE001 - keep the previous parameters if a refit fails
                    failures[m] += 1
                    if m not in last_params:
                        continue
                    h = _block_variance(m, last_params[m], r, s, e, init_var)
                    if not (np.all(np.isfinite(h)) and np.all(h > 0)):
                        continue
                forecasts[m][s:e] = h
            if progress:
                progress(k + 1, len(starts))

    return {
        "forecast_start": window,
        "forecasts": {m: v[window:] for m, v in forecasts.items()},
        "failures": failures,
        "non_converged": non_converged,
    }


# ---------------------------------------------------------------- losses and tests


def qlike(proxy: np.ndarray, h: np.ndarray) -> np.ndarray:
    ratio = proxy / h
    return ratio - np.log(ratio) - 1.0


def mse(proxy: np.ndarray, h: np.ndarray) -> np.ndarray:
    return (proxy - h) ** 2


def diebold_mariano(loss_benchmark: np.ndarray, loss_model: np.ndarray) -> dict | None:
    """Two sided test of equal expected loss. Positive mean_difference means the model has the lower loss."""
    d = np.asarray(loss_benchmark) - np.asarray(loss_model)
    n = len(d)
    if n < 30:
        return None
    dbar = d.mean()
    lags = max(1, int(n ** (1 / 3)))
    dc = d - dbar
    gamma0 = float(np.dot(dc, dc) / n)
    var = gamma0
    for k in range(1, lags + 1):
        gk = float(np.dot(dc[k:], dc[:-k]) / n)
        var += 2.0 * (1.0 - k / (lags + 1.0)) * gk
    if not var > 0:
        return None
    stat = dbar / math.sqrt(var / n) * math.sqrt((n - 1) / n)  # Harvey, Leybourne and Newbold
    p = float(2.0 * stats.t.sf(abs(stat), df=n - 1))
    return {"mean_difference": float(dbar), "statistic": float(stat), "p_value": p}


def _bootstrap_means(L: np.ndarray, draws: int, block: int, rng: np.random.Generator) -> np.ndarray:
    n = L.shape[0]
    nblocks = -(-n // block)
    starts = rng.integers(0, n, size=(draws, nblocks))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(draws, -1)[:, :n]
    return L[idx].mean(axis=1)


def model_confidence_set(L: np.ndarray, alpha: float = MCS_ALPHA, draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> np.ndarray:
    """MCS p values for the columns of the loss matrix L (n by m). A model is in the 1 - alpha set when its p value >= alpha."""
    n, m = L.shape
    rng = np.random.default_rng(seed)
    block = max(2, int(n ** (1 / 3)))
    Lbar = L.mean(axis=0)
    Lboot = _bootstrap_means(L, draws, block, rng)

    active = list(range(m))
    pvals = np.zeros(m)
    running = 0.0
    while len(active) > 1:
        idx = np.array(active)
        d_i = Lbar[idx] - Lbar[idx].mean()
        d_b = Lboot[:, idx] - Lboot[:, idx].mean(axis=1, keepdims=True)
        var_i = d_b.var(axis=0, ddof=1)
        var_i = np.where(var_i > 0, var_i, np.inf)
        t_i = d_i / np.sqrt(var_i)
        t_max = t_i.max()
        t_boot = ((d_b - d_i) / np.sqrt(var_i)).max(axis=1)
        p = float((t_boot >= t_max).mean())
        running = max(running, p)
        worst = int(idx[int(np.argmax(t_i))])
        if p >= alpha:
            break
        pvals[worst] = running
        active.remove(worst)
    for j in active:
        # a lone survivor is never eliminated, so it gets p = 1
        pvals[j] = 1.0 if len(active) == 1 else running
    return pvals


# ---------------------------------------------------------------- evaluation of a stored payload


def evaluate(payload: dict, proxy: str = "parkinson", benchmark: str = "sgarch", alpha: float = MCS_ALPHA) -> dict:
    """Losses, ranks, Diebold Mariano tests and the Model Confidence Set from stored forecasts."""
    if proxy not in PROXIES:
        raise ValueError(f"unknown proxy {proxy}")
    forecasts = {m: np.asarray(v, dtype=float) for m, v in payload["forecasts"].items()}
    usable = [m for m in MODEL_ORDER if m in forecasts and np.isfinite(forecasts[m]).mean() > 0.5]
    excluded = [m for m in MODEL_ORDER if m not in usable]
    if benchmark not in usable:
        raise ValueError("benchmark model has no forecasts")

    H = np.column_stack([forecasts[m] for m in usable])
    px = np.asarray(payload["proxies"][proxy], dtype=float)
    r2 = np.asarray(payload["proxies"]["squared_return"], dtype=float)
    mask = np.isfinite(H).all(axis=1) & np.isfinite(px) & (px > 0) & np.isfinite(r2)
    dates = np.asarray(payload["dates"])[mask]
    H, px, r2 = H[mask], px[mask], r2[mask]
    if len(px) < 60:
        raise ValueError("too few usable forecast days")

    scale = 1.0
    if proxy != "squared_return":
        scale = float(r2.mean() / px.mean())
        px = px * scale

    Lq = qlike(px[:, None], H)
    Lm = mse(px[:, None], H)
    b = usable.index(benchmark)

    def mcs(L):
        return model_confidence_set(L, alpha)

    pq, pm = mcs(Lq), mcs(Lm)
    mean_q, mean_m = Lq.mean(axis=0), Lm.mean(axis=0)
    rank_q = mean_q.argsort().argsort() + 1
    rank_m = mean_m.argsort().argsort() + 1

    rows = []
    for j, m in enumerate(usable):
        rows.append({
            "id": m,
            "name": vol.NAMES[m],
            "mean_qlike": float(mean_q[j]),
            "mean_mse": float(mean_m[j]),
            "rank_qlike": int(rank_q[j]),
            "rank_mse": int(rank_m[j]),
            "dm_qlike": None if j == b else diebold_mariano(Lq[:, b], Lq[:, j]),
            "dm_mse": None if j == b else diebold_mariano(Lm[:, b], Lm[:, j]),
            "mcs_p_qlike": float(pq[j]),
            "mcs_p_mse": float(pm[j]),
            "in_mcs_qlike": bool(pq[j] >= alpha),
            "in_mcs_mse": bool(pm[j] >= alpha),
            "failures": int(payload["failures"].get(m, 0)),
            "non_converged": int(payload["non_converged"].get(m, 0)),
        })
    rows.sort(key=lambda x: x["rank_qlike"])

    cum = {m: np.cumsum(Lq[:, b] - Lq[:, j]).round(4).tolist() for j, m in enumerate(usable) if j != b}
    return {
        "proxy": proxy,
        "scale_factor": scale,
        "observations": int(len(px)),
        "dropped": int(len(mask) - mask.sum()),
        "first_date": str(dates[0]),
        "last_date": str(dates[-1]),
        "benchmark": benchmark,
        "mcs_alpha": alpha,
        "models": rows,
        "excluded": excluded,
        "cumulative": {"dates": [str(d) for d in dates], "series": cum},
    }
