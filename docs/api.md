
## Statistics endpoint (phase 7)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/stocks/{symbol}/statistics | Summary statistics, histogram, Q-Q data, six hypothesis tests, ACF and PACF |

Parameters: period (default 5y), start, end, exchange. Returns 422 insufficient_data when the window has fewer than 60 returns. Each test returns id, name, applied_to, null_hypothesis, statistic, p_value, reject_null, alpha, interpretation and details.


## Risk endpoint (phase 8)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/stocks/{symbol}/risk | Ratios, drawdown, VaR and expected shortfall, VaR backtest, rolling volatility, GARCH(1,1) |

Parameters: period (default 5y), start, end, exchange, risk_free (annual rate in percent, 0 to 30, default 0). Returns 422 insufficient_data below 60 returns. `garch` is null below 500 returns and `backtests` is empty below 350 returns.


## Volatility models endpoint (phase 9)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/stocks/{symbol}/volatility-models | Fits sGARCH, EGARCH, GJR-GARCH, FIGARCH, fGARCH and APARCH and compares them |

Parameters: period (default 5y), start, end, exchange. Returns 422 insufficient_data below 500 daily returns. The response holds shared `dates`, a 21 day `realised_21d` series and one entry per model with parameters, log likelihood, AIC, BIC, persistence, half life, standardised residual tests, the fitted annualised volatility path, a 10 day forecast and a news impact curve (null for FIGARCH). A model that fails to fit is returned with `converged` false and an `error` message instead of failing the whole request. Results are cached in the API process per stock and window.


## Forecast evaluation endpoint (phase 10)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/stocks/{symbol}/forecast-evaluation | Out of sample losses, ranks, Diebold Mariano tests and Model Confidence Set for the six volatility models |

Parameters: proxy (parkinson, garman_klass or squared_return, default parkinson), exchange. The result is read from the table `volatility_evaluations`, which is filled by `python -m app.scripts.evaluate`. Returns 404 evaluation_not_found when no run is stored for the stock. Losses and tests are computed on request from the stored forecasts, so changing the proxy needs no new run.
