import numpy as np
import pytest


def test_indicators_sma_and_ema(client):
    r = client.get("/api/v1/stocks/NPN/indicators", params={"period": "max", "sma": "3", "ema": "3"})
    assert r.status_code == 200
    sma, ema = r.json()["data"]
    assert sma["name"] == "SMA 3" and len(sma["points"]) == 8  # 10 bars, 2 warm up
    assert sma["points"][0]["value"] == pytest.approx(101.0)
    assert sma["points"][-1]["value"] == pytest.approx((107 + 100 + 110) / 3)
    assert ema["kind"] == "ema" and ema["points"][0]["value"] == pytest.approx(101.25)


def test_indicators_use_history_before_the_window(client):
    # Window starts 2026-01-14 but SMA 3 on that date still uses the two earlier bars.
    r = client.get("/api/v1/stocks/NPN/indicators", params={"start": "2026-01-14", "sma": "3", "ema": ""})
    points = r.json()["data"][0]["points"]
    assert points[0]["date"] == "2026-01-14" and points[0]["value"] == pytest.approx((105 + 106 + 107) / 3)


def test_indicators_reject_bad_windows(client):
    for bad in ["abc", "1", "401", "2,3,4,5,6,7,8"]:
        r = client.get("/api/v1/stocks/NPN/indicators", params={"sma": bad})
        assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_parameter"


def test_indicators_empty_lists_are_allowed(client):
    r = client.get("/api/v1/stocks/NPN/indicators", params={"sma": "", "ema": ""})
    assert r.status_code == 200 and r.json()["data"] == []


def test_performance_values(client):
    r = client.get("/api/v1/stocks/NPN/performance", params={"period": "max"})
    body = r.json()
    s = body["data"]["summary"]
    closes = np.array([100, 101, 102, 103, 104, 105, 106, 107, 100, 110], dtype=float)
    logret = np.diff(np.log(closes))
    assert s["observations"] == 9
    assert s["total_return_pct"] == pytest.approx(10.0)
    assert s["annualised_volatility_pct"] == pytest.approx(np.std(logret, ddof=1) * np.sqrt(252) * 100)
    assert s["best_day"]["date"] == "2026-01-16" and s["best_day"]["value"] == pytest.approx(np.log(1.1) * 100)
    assert s["worst_day"]["date"] == "2026-01-15"
    assert len(body["data"]["cumulative_return"]) == 10 and len(body["data"]["daily_returns"]) == 9
    assert body["data"]["cumulative_return"][0]["value"] == 0.0
    assert body["meta"]["price_basis"] == "adjusted close"


def test_performance_needs_enough_history(client):
    r = client.get("/api/v1/stocks/NPN/performance", params={"start": "2026-01-15"})  # 2 bars
    assert r.status_code == 422 and r.json()["error"]["code"] == "insufficient_data"


def test_performance_unknown_stock(client):
    assert client.get("/api/v1/stocks/ZZZZ/performance").status_code == 404
