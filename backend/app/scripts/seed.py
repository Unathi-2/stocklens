"""Seed a starter universe. Safe to run repeatedly.

Run from the backend folder:  python -m app.scripts.seed

Provider symbols for the JSE (.JO suffix) and indices are placeholders until
they are verified against the data provider in Phase 3.
"""
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Company

# (symbol, provider_symbol, name, exchange, asset_type, currency, country)
UNIVERSE = [
    ("J203", "^J203.JO", "FTSE/JSE All Share Index", "JSE", "index", "ZAR", "South Africa"),
    ("NPN", "NPN.JO", "Naspers", "JSE", "equity", "ZAR", "South Africa"),
    ("PRX", "PRX.JO", "Prosus", "JSE", "equity", "ZAR", "South Africa"),
    ("SBK", "SBK.JO", "Standard Bank Group", "JSE", "equity", "ZAR", "South Africa"),
    ("FSR", "FSR.JO", "FirstRand", "JSE", "equity", "ZAR", "South Africa"),
    ("MTN", "MTN.JO", "MTN Group", "JSE", "equity", "ZAR", "South Africa"),
    ("SOL", "SOL.JO", "Sasol", "JSE", "equity", "ZAR", "South Africa"),
    ("SHP", "SHP.JO", "Shoprite Holdings", "JSE", "equity", "ZAR", "South Africa"),
    ("GSPC", "^GSPC", "S&P 500 Index", "NYSE", "index", "USD", "United States"),
    ("AAPL", "AAPL", "Apple Inc.", "NASDAQ", "equity", "USD", "United States"),
    ("MSFT", "MSFT", "Microsoft Corporation", "NASDAQ", "equity", "USD", "United States"),
    ("NVDA", "NVDA", "NVIDIA Corporation", "NASDAQ", "equity", "USD", "United States"),
]


def main() -> None:
    added = 0
    with SessionLocal() as db:
        for symbol, provider_symbol, name, exchange, asset_type, currency, country in UNIVERSE:
            exists = db.scalar(select(Company).where(Company.provider_symbol == provider_symbol))
            if exists:
                continue
            db.add(
                Company(
                    symbol=symbol,
                    provider_symbol=provider_symbol,
                    name=name,
                    exchange=exchange,
                    asset_type=asset_type,
                    currency=currency,
                    country=country,
                )
            )
            added += 1
        db.commit()
    print(f"Seed complete. Added {added}, skipped {len(UNIVERSE) - added}.")


if __name__ == "__main__":
    main()
