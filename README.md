# StockLens

An interactive analytics platform for exploring JSE and US equities, measuring risk, and experimenting with statistical and machine learning volatility models.

StockLens is an analytics application. It does not trade, and it does not tell anyone what to buy.

## Status

Phase 1 complete when this scaffold runs. See docs/roadmap.md for the full plan.

## Planned features

- Market overview for the JSE All Share and US indices
- Stock search, profiles, price history and technical indicators
- Return and distribution analysis with ADF, ARCH LM, Jarque Bera and Ljung Box tests
- Risk metrics: volatility, drawdown, VaR, Expected Shortfall
- Volatility modelling with GARCH, EGARCH and GJR GARCH under several error distributions
- Forecast comparison of naive, ARIMA, GARCH, LSTM and a GARCH LSTM hybrid
- Paper portfolios and watchlists

## Tech stack

React, TypeScript, Tailwind CSS, FastAPI, SQLAlchemy, PostgreSQL, statsmodels, arch, Docker.

## Run it in GitHub Codespaces

1. Open the repository in a Codespace. The dev container installs dependencies.
2. Start the database: `docker compose up -d db`
3. Backend: `cd backend && uvicorn app.main:app --reload`
4. Frontend, in a second terminal: `cd frontend && npm run dev`
5. Open the forwarded port 5173. The sidebar page should show "API: online".

Run the tests with `cd backend && pytest -q`.

Or run everything with `docker compose up`.

## Project layout

- backend/app/api: HTTP routes only
- backend/app/services: orchestration, database and market data providers
- backend/app/analytics: pure statistical functions, no web code
- frontend/src: React application
- docs: product definition, architecture, roadmap

## Disclaimer

For education and research. Nothing here is financial advice.
