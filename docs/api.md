
## Chart and analytics endpoints (phase 6)

| Method | Path | Purpose |
|---|---|---|
| GET | /api/v1/stocks/{symbol}/indicators | Simple and exponential moving averages |
| GET | /api/v1/stocks/{symbol}/performance | Return and volatility summary with cumulative and daily return series |

indicators parameters: period, interval, start, end, sma (default 20,50,200), ema (default 20), exchange. Windows must be whole numbers from 2 to 400, at most 6 per list. Empty lists are allowed.

performance parameters: period, start, end, exchange. Always uses daily adjusted closes. Returns 422 insufficient_data when the window has fewer than 3 prices.

See docs/methodology.md for the formulas.
