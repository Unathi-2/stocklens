# Market data pipeline

    Provider (yfinance) -> validation -> PostgreSQL

## Components

1. services/market_data.py defines the MarketDataProvider interface.
2. services/providers/yfinance_provider.py is the current implementation.
3. services/validation.py cleans bars and produces a report.
4. services/ingestion.py stores new bars. It is incremental and idempotent.
5. scripts/ingest.py is the command line entry point.

## Validation rules

Drop duplicates, missing or non positive prices, negative volume, and bars where high is below low. Calendar gaps over 7 days are reported, not removed. Prices keep the raw close plus a separate adjusted close.

## Run

    cd backend
    alembic upgrade head
    python -m app.scripts.seed
    python -m app.scripts.ingest --years 5 --profiles

## Known risks

1. JSE and index symbols in the seed list are unverified. If a symbol fails, the ingest output shows FAIL and the batch continues. Fix provider_symbol in the seed file or the database.
2. yfinance is unofficial and can break or rate limit. Re-running is safe.
3. Check the data provider terms before publishing the app.
