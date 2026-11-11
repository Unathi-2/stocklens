def test_risk_endpoint_shape(long_client):
    r = long_client.get("/api/v1/stocks/LONG/risk", params={"period": "max", "risk_free": 7})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["summary"]["risk_free_pct"] == 7
    assert d["drawdown"]["max_drawdown_pct"] <= 0 and d["drawdown"]["series"]
    assert [w["window"] for w in d["rolling_volatility"]] == [21, 63]
    assert [v["confidence"] for v in d["var"]] == [0.95, 0.99]
    assert d["garch"] is None  # 399 returns is below the 500 needed
    assert r.json()["meta"]["garch_minimum_observations"] == 500


def test_risk_needs_enough_history(client):
    r = client.get("/api/v1/stocks/NPN/risk", params={"period": "max"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "insufficient_data"


def test_risk_rejects_bad_risk_free_rate(long_client):
    assert long_client.get("/api/v1/stocks/LONG/risk", params={"risk_free": -1}).status_code == 422


def test_risk_unknown_stock(client):
    assert client.get("/api/v1/stocks/ZZZZ/risk").status_code == 404
