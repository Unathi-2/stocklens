from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Company
from conftest import _bars


@pytest.fixture()
def vol_client():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    closes = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, 650)))
    with Session(engine) as db:
        company = Company(symbol="VOL", provider_symbol="VOL", name="Vol Co", exchange="NYSE", currency="USD")
        db.add(company)
        db.flush()
        db.add_all(_bars(company.id, [round(float(c), 4) for c in closes], start=date(2022, 1, 3)))
        db.commit()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_volatility_models_endpoint(vol_client):
    r = vol_client.get("/api/v1/stocks/VOL/volatility-models", params={"period": "max"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert [m["id"] for m in d["models"]] == ["sgarch", "egarch", "gjr", "figarch", "fgarch", "aparch"]
    assert d["observations"] == 649 and len(d["dates"]) == 649
    assert len(d["forecast_dates"]) == d["horizon"] == 10
    assert d["best_aic"] in {m["id"] for m in d["models"]}
    # cached: the second call returns the same payload
    assert vol_client.get("/api/v1/stocks/VOL/volatility-models", params={"period": "max"}).json() == r.json()


def test_volatility_models_need_enough_history(long_client):
    r = long_client.get("/api/v1/stocks/LONG/volatility-models", params={"period": "max"})  # 399 returns
    assert r.status_code == 422 and r.json()["error"]["code"] == "insufficient_data"


def test_volatility_models_unknown_stock(client):
    assert client.get("/api/v1/stocks/ZZZZ/volatility-models").status_code == 404
