from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models import Company, PriceHistory


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def make_company(**overrides) -> Company:
    values = dict(
        symbol="NPN", provider_symbol="NPN.JO", name="Naspers", exchange="JSE", currency="ZAR"
    )
    values.update(overrides)
    return Company(**values)


def make_bar(company_id: int, d: date, close: str = "100") -> PriceHistory:
    c = Decimal(close)
    return PriceHistory(
        company_id=company_id, date=d, open=c, high=c, low=c, close=c, adjusted_close=c, volume=10
    )


def test_insert_and_retrieve_company_with_prices(db):
    company = make_company()
    db.add(company)
    db.flush()
    db.add_all([make_bar(company.id, date(2026, 1, 2)), make_bar(company.id, date(2026, 1, 5), "101")])
    db.commit()

    loaded = db.scalar(select(Company).where(Company.symbol == "NPN"))
    assert len(loaded.prices) == 2


def test_duplicate_symbol_on_same_exchange_rejected(db):
    db.add(make_company())
    db.commit()
    db.add(make_company(provider_symbol="NPN2.JO"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_duplicate_price_date_rejected(db):
    company = make_company()
    db.add(company)
    db.flush()
    db.add(make_bar(company.id, date(2026, 1, 2)))
    db.commit()
    db.add(make_bar(company.id, date(2026, 1, 2)))
    with pytest.raises(IntegrityError):
        db.commit()


def test_non_positive_close_rejected(db):
    company = make_company()
    db.add(company)
    db.flush()
    db.add(make_bar(company.id, date(2026, 1, 2), close="0"))
    with pytest.raises(IntegrityError):
        db.commit()
