from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Company, VolatilityEvaluation
from app.services import evaluation_service
from conftest import _bars
from test_evaluation import make_payload


@pytest.fixture()
def env():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    rng = np.random.default_rng(4)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.012, 700)))
    with Session(engine) as db:
        company = Company(symbol="EVL", provider_symbol="EVL", name="Eval Co", exchange="NYSE", currency="USD")
        db.add(company)
        db.flush()
        db.add_all(_bars(company.id, [round(float(c), 4) for c in closes], start=date(2022, 1, 3)))
        db.commit()

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override
    yield engine, TestClient(app)
    app.dependency_overrides.clear()


def store_fake(engine):
    with Session(engine) as db:
        company = db.scalar(select(Company))
        db.add(VolatilityEvaluation(
            company_id=company.id, window=500, refit_every=20, data_end=date(2025, 1, 1),
            n_forecasts=500, payload=make_payload(500),
        ))
        db.commit()


def test_endpoint_returns_losses_and_tests(env):
    engine, client = env
    store_fake(engine)
    r = client.get("/api/v1/stocks/EVL/forecast-evaluation", params={"proxy": "garman_klass"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["proxy"] == "garman_klass" and d["benchmark"] == "sgarch" and d["observations"] == 500
    assert [m["rank_qlike"] for m in d["models"]] == [1, 2, 3, 4, 5, 6]
    assert d["models"][-1]["id"] == "sgarch" and d["models"][-1]["dm_qlike"] is None
    assert len(d["cumulative"]["dates"]) == 500 and "sgarch" not in d["cumulative"]["series"]


def test_endpoint_errors(env):
    engine, client = env
    r = client.get("/api/v1/stocks/EVL/forecast-evaluation")
    assert r.status_code == 404 and r.json()["error"]["code"] == "evaluation_not_found"
    assert "python -m app.scripts.evaluate --symbols EVL" in r.json()["error"]["message"]
    store_fake(engine)
    assert client.get("/api/v1/stocks/EVL/forecast-evaluation", params={"proxy": "bad"}).status_code == 422
    assert client.get("/api/v1/stocks/ZZZ/forecast-evaluation").status_code == 404


def test_run_and_store_round_trip(env):
    engine, client = env
    with Session(engine) as db:
        company = db.scalar(select(Company))
        row = evaluation_service.run_evaluation(db, company, window=300, refit_every=200)
        assert row.n_forecasts == 399 and row.data_end == date.fromisoformat(row.payload["dates"][-1])
        row2 = evaluation_service.run_evaluation(db, company, window=300, refit_every=200)  # replaces, not duplicates
        assert row2.id == row.id
    r = client.get("/api/v1/stocks/EVL/forecast-evaluation", params={"proxy": "squared_return"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["window"] == 300 and d["refit_every"] == 200 and len(d["models"]) == 6
