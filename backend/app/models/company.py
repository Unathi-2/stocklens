from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Company(Base):
    """A tradable instrument: equity, ETF or index."""

    __tablename__ = "companies"
    __table_args__ = (UniqueConstraint("symbol", "exchange", name="uq_company_symbol_exchange"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)  # display symbol, e.g. NPN
    provider_symbol: Mapped[str] = mapped_column(String(30), unique=True)  # source symbol, e.g. NPN.JO
    name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(20))  # JSE, NASDAQ, NYSE
    asset_type: Mapped[str] = mapped_column(String(10), default="equity")  # equity, etf, index
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(60))
    currency: Mapped[str] = mapped_column(String(3))  # ZAR, USD
    market_cap: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    prices: Mapped[list["PriceHistory"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
