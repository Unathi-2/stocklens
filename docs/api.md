
## Statistics endpoint (phase 7)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/stocks/{symbol}/statistics | Summary statistics, histogram, Q-Q data, six hypothesis tests, ACF and PACF |

Parameters: period (default 5y), start, end, exchange. Returns 422 insufficient_data when the window has fewer than 60 returns. Each test returns id, name, applied_to, null_hypothesis, statistic, p_value, reject_null, alpha, interpretation and details.
