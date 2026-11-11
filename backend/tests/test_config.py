from app.core.config import Settings


def test_database_url_gets_driver():
    assert Settings(database_url="postgres://u:p@h/db").database_url == "postgresql+psycopg://u:p@h/db"
    assert Settings(database_url="postgresql://u:p@h/db?sslmode=require").database_url == (
        "postgresql+psycopg://u:p@h/db?sslmode=require"
    )
    assert Settings(database_url="postgresql+psycopg://u:p@h/db").database_url == "postgresql+psycopg://u:p@h/db"


def test_cors_origins_accepts_csv_and_json(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.vercel.app/, https://b.dev")
    assert Settings().cors_origins == ["https://a.vercel.app", "https://b.dev"]
    monkeypatch.setenv("CORS_ORIGINS", '["https://c.dev"]')
    assert Settings().cors_origins == ["https://c.dev"]
