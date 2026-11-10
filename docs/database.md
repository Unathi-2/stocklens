# Database design

Phase 2 covers the market data core. User, portfolio and analysis tables arrive in later phases.

## ERD

```mermaid
erDiagram
    companies ||--o{ price_history : has
    companies {
        int id PK
        string symbol
        string provider_symbol UK
        string name
        string exchange
        string asset_type
        string sector
        string industry
        string country
        string currency
        bigint market_cap
        timestamptz created_at
        timestamptz updated_at
    }
    price_history {
        int id PK
        int company_id FK
        date date
        numeric open
        numeric high
        numeric low
        numeric close
        numeric adjusted_close
        bigint volume
        timestamptz created_at
    }
```

## Decisions

- symbol is the display symbol (NPN). provider_symbol is what the data source expects (NPN.JO), so the provider can change without renaming companies.
- Indices live in companies with asset_type "index", so they share the price pipeline.
- currency is stored per company (ZAR or USD). Returns are computed per instrument in its own currency.
- Unique (symbol, exchange) on companies and unique (company_id, date) on price_history. The second also acts as the lookup index.
- Check constraints guard against bad data: positive close, non negative volume, high not below low.
- Prices use Numeric(18, 6) rather than floats, to avoid rounding drift in storage.

## Workflow

    cd backend
    alembic revision --autogenerate -m "create companies and price history"
    alembic upgrade head
    python -m app.scripts.seed
