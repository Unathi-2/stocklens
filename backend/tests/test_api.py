from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.market_status import exchange_status


def test_search_by_name_and_symbol(client):
    r = client.get("/api/v1/stocks/search", params={"q": "naspers"})
    assert r.status_code == 200
    assert [c["symbol"] for c in r.json()["data"]] == ["NPN"]
    r = client.get("/api/v1/stocks/search", params={"q": "aap"})
    assert r.json()["data"][0]["symbol"] == "AAPL"


def test_search_requires_query(client):
    assert client.get("/api/v1/stocks/search").status_code == 422


def test_get_stock_case_insensitive(client):
    r = client.get("/api/v1/stocks/npn")
    assert r.status_code == 200 and r.json()["data"]["exchange"] == "JSE"


def test_unknown_stock_returns_404_envelope(client):
    r = client.get("/api/v1/stocks/ZZZZ")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "stock_not_found"


def test_quote_values(client):
    q = client.get("/api/v1/stocks/NPN/quote").json()["data"]
    assert q["price"] == 110.0 and q["previous_close"] == 100.0
    assert round(q["change_pct"], 6) == 10.0
    assert q["week52_high"] == 111.0 and q["week52_low"] == 99.0


def test_quote_without_data_is_404(client):
    r = client.get("/api/v1/stocks/EMPTY/quote")
    assert r.status_code == 404 and r.json()["error"]["code"] == "no_price_data"


def test_profile_counts_observations(client):
    p = client.get("/api/v1/stocks/NPN/profile").json()["data"]
    assert p["observations"] == 10 and p["data_start"] == "2026-01-05"


def test_history_daily_and_meta(client):
    r = client.get("/api/v1/stocks/NPN/history", params={"period": "max"})
    body = r.json()
    assert body["meta"]["count"] == 10 and body["meta"]["currency"] == "ZAR"
    dates = [b["date"] for b in body["data"]]
    assert dates == sorted(dates)


def test_history_date_range_overrides_period(client):
    r = client.get(
        "/api/v1/stocks/NPN/history", params={"start": "2026-01-12", "end": "2026-01-14"}
    )
    assert [b["date"] for b in r.json()["data"]] == ["2026-01-12", "2026-01-13", "2026-01-14"]


def test_history_weekly_resample(client):
    r = client.get("/api/v1/stocks/NPN/history", params={"period": "max", "interval": "1wk"})
    weeks = r.json()["data"]
    assert len(weeks) == 2
    assert weeks[0]["open"] == 100.0 and weeks[0]["close"] == 104.0
    assert weeks[0]["volume"] == 5000 and weeks[0]["date"] == "2026-01-09"


def test_history_rejects_bad_period(client):
    assert client.get("/api/v1/stocks/NPN/history", params={"period": "9y"}).status_code == 422


def test_markets_lists_indices_only(client):
    data = client.get("/api/v1/markets").json()["data"]
    assert [q["symbol"] for q in data] == ["J203"]


def test_movers_ordering(client):
    data = client.get("/api/v1/markets/movers", params={"exchange": "JSE"}).json()["data"]
    assert data["gainers"][0]["symbol"] == "NPN" and round(data["gainers"][0]["change_pct"], 6) == 10.0
    assert data["gainers"][0]["currency"] == "ZAR"
    assert data["losers"][0]["symbol"] == "SBK" and round(data["losers"][0]["change_pct"], 6) == -5.0


def test_exchange_status_open_and_closed():
    open_jse = datetime(2026, 11, 10, 8, 0, tzinfo=ZoneInfo("UTC"))  # 10:00 in Johannesburg, Tuesday
    status = {s.exchange: s for s in exchange_status(open_jse)}
    assert status["JSE"].is_open and not status["NYSE"].is_open

    saturday = datetime(2026, 11, 14, 8, 0, tzinfo=ZoneInfo("UTC"))
    assert not any(s.is_open for s in exchange_status(saturday))


def test_status_endpoint_shape(client):
    r = client.get("/api/v1/markets/status")
    assert r.status_code == 200 and len(r.json()["data"]) == 3
