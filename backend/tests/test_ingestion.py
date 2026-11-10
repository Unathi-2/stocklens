from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Company, PriceHistory
from app.services.ingestion import ingest_company
from app.services.market_data import MarketDataProvider, PriceBar


class FakeProvider(MarketDataProvider):
    def __init__(self, bars, fail=False):
        self.bars, self.fail, self.calls = bars, fail, []

    def search_symbols(self, query):
        return []

    def get_history(self, symbol, start, end):
        self.calls.append((start, end))
        if self.fail:
            raise RuntimeError("provider down")
        return [b for b in self.bars if start <= b.date <= end]

    def get_profile(self, symbol):
        return {"sector": "Technology"}


def mk(d, c=10.0):
    return PriceBar(date=d, open=c, high=c, low=c, close=c, adjusted_close=c, volume=1)


@pytest.fixture()
def db_company():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        company = Company(
            symbol="NPN", provider_symbol="NPN.JO", name="Naspers", exchange="JSE", currency="ZAR"
        )
        db.add(company)
        db.commit()
        yield db, company


def count(db):
    return db.scalar(select(func.count()).select_from(PriceHistory))


def test_ingest_inserts_and_is_idempotent(db_company):
    db, company = db_company
    provider = FakeProvider([mk(date(2026, 1, 2)), mk(date(2026, 1, 5))])
    r1 = ingest_company(db, provider, company, date(2026, 1, 1), date(2026, 1, 31))
    assert r1.inserted == 2 and count(db) == 2
    r2 = ingest_company(db, provider, company, date(2026, 1, 1), date(2026, 1, 31))
    assert r2.inserted == 0 and count(db) == 2


def test_second_run_only_requests_new_dates(db_company):
    db, company = db_company
    provider = FakeProvider([mk(date(2026, 1, 2)), mk(date(2026, 1, 20))])
    ingest_company(db, provider, company, date(2026, 1, 1), date(2026, 1, 10))
    ingest_company(db, provider, company, date(2026, 1, 1), date(2026, 1, 31))
    assert provider.calls[1][0] == date(2026, 1, 3)
    assert count(db) == 2


def test_provider_failure_is_reported_not_raised(db_company):
    db, company = db_company
    result = ingest_company(db, FakeProvider([], fail=True), company, date(2026, 1, 1), date(2026, 1, 31))
    assert result.error == "provider down" and count(db) == 0


def test_profile_refresh_updates_company(db_company):
    db, company = db_company
    provider = FakeProvider([mk(date(2026, 1, 2))])
    ingest_company(db, provider, company, date(2026, 1, 1), date(2026, 1, 31), refresh_profile=True)
    assert company.sector == "Technology"
