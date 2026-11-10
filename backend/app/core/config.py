from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://stocklens:stocklens@localhost:5432/stocklens"
    cors_origins: list[str] = ["http://localhost:5173"]
    market_data_provider: str = "yfinance"


settings = Settings()
