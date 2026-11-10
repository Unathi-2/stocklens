from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Company, PriceHistory


def _bars(company_id, closes, start=date(2026, 1, 5)):
    """Consecutive weekdays starting Monday 5 Jan 2026."""
    out, d = [], start
    for c in closes:
        while d.weekday() >= 5:
            d = date.fromordinal(d.toordinal() + 1)
        v = Decimal(str(c))
        out.append(
            PriceHistory(
                company_id=company_id, date=d, open=v, high=v + 1, low=v - 1,
                close=v, adjusted_close=v, volume=1000,
            )
        )
        d = date.fromordinal(d.toordinal() + 1)
    return out


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        companies = [
            Company(symbol="NPN", provider_symbol="NPN.JO", name="Naspers", exchange="JSE", currency="ZAR"),
            Company(symbol="SBK", provider_symbol="SBK.JO", name="Standard Bank Group", exchange="JSE", currency="ZAR"),
            Company(symbol="J203", provider_symbol="^J203.JO", name="FTSE/JSE All Share Index",
                    exchange="JSE", asset_type="index", currency="ZAR"),
            Company(symbol="AAPL", provider_symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", currency="USD"),
            Company(symbol="EMPTY", provider_symbol="EMPTY", name="No Data Co", exchange="NYSE", currency="USD"),
        ]
        db.add_all(companies)
        db.flush()
        ids = {c.symbol: c.id for c in companies}
        # 10 weekdays each, last day up for NPN (+10%), down for SBK (-5%)
        db.add_all(_bars(ids["NPN"], [100, 101, 102, 103, 104, 105, 106, 107, 100, 110]))
        db.add_all(_bars(ids["SBK"], [50, 50, 50, 50, 50, 50, 50, 50, 100, 95]))
        db.add_all(_bars(ids["J203"], [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1010]))
        db.add_all(_bars(ids["AAPL"], [200, 201, 202, 203, 204, 205, 206, 207, 208, 209]))
        db.commit()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
