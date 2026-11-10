# API reference

Interactive docs: run the backend and open /docs (Swagger) or /redoc.

All successful responses use the shape {"data": ..., "meta": {...}}.
All errors use {"error": {"code": "...", "message": "..."}}.

| Method | Path | Purpose |
|---|---|---|
| GET | /health | Liveness check |
| GET | /api/v1/stocks/search?q= | Search by symbol or name |
| GET | /api/v1/stocks/{symbol} | Instrument details |
| GET | /api/v1/stocks/{symbol}/profile | Details plus data coverage |
| GET | /api/v1/stocks/{symbol}/quote | Latest stored close, change, 52 week range |
| GET | /api/v1/stocks/{symbol}/history | Daily, weekly or monthly bars |
| GET | /api/v1/markets | Index quotes (JSE All Share, S&P 500) |
| GET | /api/v1/markets/status | Open or closed per exchange |
| GET | /api/v1/markets/movers | Top gainers and losers |

History parameters: period (1m, 3m, 6m, 1y, 5y, max), interval (1d, 1wk, 1mo), start, end (dates, override period), exchange.

Errors: 404 stock_not_found, 404 no_price_data, 409 ambiguous_symbol (add ?exchange=), 422 invalid parameters.

Notes
1. Quotes are the latest stored daily close, not real time.
2. Market status ignores public holidays.
3. Weekly bars are dated by the last trading day of the week.
