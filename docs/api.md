
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
