"""Download and store price history.

Run from the backend folder:
    python -m app.scripts.ingest --years 5
    python -m app.scripts.ingest --symbols NPN AAPL --years 10 --profiles
"""
import argparse
from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Company
from app.services.ingestion import ingest_company
from app.services.providers.factory import get_provider


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest historical prices")
    parser.add_argument("--symbols", nargs="*", help="display symbols; default is every company")
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--profiles", action="store_true", help="also refresh sector and market cap")
    args = parser.parse_args()

    end = date.today()
    start = end - timedelta(days=365 * args.years)
    provider = get_provider()

    with SessionLocal() as db:
        query = select(Company).order_by(Company.exchange, Company.symbol)
        if args.symbols:
            query = query.where(Company.symbol.in_(args.symbols))
        companies = list(db.scalars(query))
        if not companies:
            print("No companies found. Run: python -m app.scripts.seed")
            return

        for company in companies:
            result = ingest_company(db, provider, company, start, end, refresh_profile=args.profiles)
            if result.error:
                print(f"FAIL  {result.symbol:12} {result.error}")
                continue
            r = result.report
            print(
                f"OK    {result.symbol:12} inserted={result.inserted:5} "
                f"dropped={r.dropped} (dup={r.duplicates} bad={r.invalid_prices} "
                f"vol={r.negative_volume} hl={r.high_below_low}) gaps={len(r.gaps)}"
            )


if __name__ == "__main__":
    main()
