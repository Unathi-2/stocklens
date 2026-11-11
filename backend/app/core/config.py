from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://stocklens:stocklens@localhost:5432/stocklens"
    # Accepts a JSON list or a comma separated string, so hosting dashboards are easy to fill in.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    market_data_provider: str = "yfinance"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg3_driver(cls, value: str) -> str:
        """Hosts such as Neon hand out postgres:// or postgresql:// URLs; SQLAlchemy needs the driver named."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                import json

                return json.loads(text)
            return [item.strip().rstrip("/") for item in text.split(",") if item.strip()]
        return value


settings = Settings()
