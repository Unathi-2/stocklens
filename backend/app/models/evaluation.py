from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VolatilityEvaluation(Base):
    """Stored result of a rolling forecast run: one row per company, replaced on every run.

    The payload holds the out of sample variance forecasts of each model and the realised variance proxies.
    Losses and tests are computed from it when the API is called, so the choice of proxy stays flexible.
    """

    __tablename__ = "volatility_evaluations"
    __table_args__ = (UniqueConstraint("company_id", name="uq_volatility_evaluation_company"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    window: Mapped[int] = mapped_column(Integer)
    refit_every: Mapped[int] = mapped_column(Integer)
    data_end: Mapped[date] = mapped_column(Date)
    n_forecasts: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict] = mapped_column(JSON)
