def test_statistics_endpoint_shape(long_client):
    r = long_client.get("/api/v1/stocks/LONG/statistics", params={"period": "max"})
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["summary"]["observations"] == 399
    assert [t["id"] for t in d["tests"]] == [
        "adf_log_price", "adf_returns", "arch_lm", "jarque_bera", "ljung_box_returns", "ljung_box_squared",
    ]
    assert len(d["qq"]["theoretical"]) == len(d["qq"]["sample"]) == 399
    assert len(d["histogram"]["bin_centers"]) == 40
    assert len(d["acf"]["lags"]) == 30
    assert r.json()["meta"]["significance_level"] == 0.05


def test_statistics_need_enough_history(client):
    r = client.get("/api/v1/stocks/NPN/statistics", params={"period": "max"})  # only 10 bars
    assert r.status_code == 422 and r.json()["error"]["code"] == "insufficient_data"


def test_statistics_unknown_stock(client):
    assert client.get("/api/v1/stocks/ZZZZ/statistics").status_code == 404
