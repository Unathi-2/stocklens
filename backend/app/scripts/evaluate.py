"""Run the rolling out of sample volatility evaluation and store it.

Run from the backend folder:
    python -m app.scripts.evaluate --symbols NPN AAPL
    python -m app.scripts.evaluate                       # every company with enough history
    python -m app.scripts.evaluate --window 750 --refit-every 40

Each stock needs about a minute with the defaults (window 500, refit every 20 days).
"""
import argparse
import time

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.errors import InsufficientData
from app.models import Company
from app.services import evaluation_service as svc


def main() -> None:
    parser = argparse.ArgumentParser(description="Rolling out of sample volatility forecast evaluation")
    parser.add_argument("--symbols", nargs="*", help="display symbols; default is every company")
    parser.add_argument("--window", type=int, default=svc.DEFAULT_WINDOW, help="estimation window in returns")
    parser.add_argument("--refit-every", type=int, default=svc.DEFAULT_REFIT_EVERY, help="days between re-estimations")
    args = parser.parse_args()

    with SessionLocal() as db:
        query = select(Company).order_by(Company.exchange, Company.symbol)
        if args.symbols:
            query = query.where(Company.symbol.in_(args.symbols))
        companies = list(db.scalars(query))
        if not companies:
            print("No companies found. Run: python -m app.scripts.seed")
            return

        for company in companies:
            t0 = time.time()
            print(f"{company.symbol:8} fitting...", end="", flush=True)

            def progress(done: int, total: int) -> None:
                print(f"\r{company.symbol:8} fitting... {done}/{total} refits", end="", flush=True)

            try:
                row = svc.run_evaluation(db, company, args.window, args.refit_every, progress)
            except InsufficientData:
                print(f"\r{company.symbol:8} SKIP  not enough history for window {args.window}")
                continue
            except Exception as exc:  # noqa: BLE001 - keep going with the next stock
                db.rollback()
                print(f"\r{company.symbol:8} FAIL  {type(exc).__name__}: {exc}")
                continue
            print(f"\r{company.symbol:8} OK    {row.n_forecasts} forecasts to {row.data_end} in {time.time() - t0:.0f}s" + " " * 10)


if __name__ == "__main__":
    main()
