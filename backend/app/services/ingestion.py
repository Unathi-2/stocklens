"""Ingestion: provider -> validation -> database.

Incremental and idempotent. Existing dates are never duplicated, so the job
can be re-run safely. Portable SQL (no dialect specific upsert) so it is
testable against SQLite as well as PostgreSQL.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Company, PriceHistory
from app.services.market_data import MarketDataProvider
from app.services.validation import ValidationReport, validate_bars


@dataclass
class IngestResult:
    symbol: str
    inserted: int
    report: ValidationReport
    error: str | None = None


def ingest_company(
    db: Session,
    provider: MarketDataProvider,
    company: Company,
    start: date,
    end: date,
    refresh_profile: bool = False,
) -> IngestResult:
    last = db.scalar(select(func.max(PriceHistory.date)).where(PriceHistory.company_id == company.id))
    if last is not None:
        start = max(start, last + timedelta(days=1))
    if start > end:
        return IngestResult(company.provider_symbol, 0, ValidationReport())

    try:
        raw = provider.get_history(company.provider_symbol, start, end)
    except Exception as exc:  # one bad symbol must not stop the batch
        return IngestResult(company.provider_symbol, 0, ValidationReport(), error=str(exc))

    clean, report = validate_bars(raw)
    existing = set(
        db.scalars(select(PriceHistory.date).where(PriceHistory.company_id == company.id))
    )
    new_rows = [
        PriceHistory(
            company_id=company.id,
            date=b.date,
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            adjusted_close=b.adjusted_close,
            volume=b.volume,
        )
        for b in clean
        if b.date not in existing
    ]
    db.add_all(new_rows)

    if refresh_profile:
        try:
            profile = provider.get_profile(company.provider_symbol)
            for key in ("sector", "industry", "market_cap"):
                if profile.get(key):
                    setattr(company, key, profile[key])
        except Exception:
            pass  # profile data is optional

    db.commit()
    return IngestResult(company.provider_symbol, len(new_rows), report)
