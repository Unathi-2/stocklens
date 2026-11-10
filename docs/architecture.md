# Architecture

## Layers

    React (frontend)
        calls
    FastAPI routes (backend/app/api)
        call
    Services (backend/app/services)
        call
    Analytics (backend/app/analytics), pure functions
    Providers and PostgreSQL

Rules:
- Routes validate input and shape output. No maths.
- Analytics never import FastAPI or SQLAlchemy, so they can be reused in notebooks and tested alone.
- The frontend never calls an external market API. API keys stay in the backend.

## Data flow

    External provider -> ingestion job -> validation -> PostgreSQL -> FastAPI -> React

Users query the local database, which avoids provider rate limits and keeps pages fast.

## Market data

The MarketDataProvider interface in backend/app/services/market_data.py hides the source. Prototype with yfinance (JSE symbols use the .JO suffix on Yahoo, to be verified in Phase 3). Check the terms of any provider before publishing the app.

## Long running models

Model endpoints will return an analysis id immediately and run in the background. Clients poll GET /analysis/{id}.

## Evaluation rules

Time ordered train, validation and test splits only.
