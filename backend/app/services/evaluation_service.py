"""Run and read out of sample volatility forecast evaluations."""
import math
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics import evaluation
from app.analytics.returns import log_returns
from app.core.errors import EvaluationNotFound, InsufficientData, InvalidParameter
from app.models import Company, PriceHistory, VolatilityEvaluation
from app.schemas.stock import EvaluationOut

DEFAULT_WINDOW = 500
DEFAULT_REFIT_EVERY = 20
MIN_FORECASTS = 100


def _frame(db: Session, company: Company) -> pd.DataFrame:
    rows = db.execute(
        select(
            PriceHistory.date, PriceHistory.open, PriceHistory.high, PriceHistory.low,
            PriceHistory.close, PriceHistory.adjusted_close,
        )
        .where(PriceHistory.company_id == company.id)
        .order_by(PriceHistory.date)
    ).all()
    df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "adjusted_close"])
    df[["open", "high", "low", "close", "adjusted_close"]] = df[["open", "high", "low", "close", "adjusted_close"]].astype(float)
    df.index = pd.to_datetime(df.pop("date"))
    return df


def _clean(values, digits=6):
    return [round(float(v), digits) if math.isfinite(float(v)) else None for v in values]


def run_evaluation(
    db: Session, company: Company, window: int = DEFAULT_WINDOW, refit_every: int = DEFAULT_REFIT_EVERY, progress=None
) -> VolatilityEvaluation:
    """Compute rolling forecasts for one company and store them, replacing any earlier run."""
    df = _frame(db, company)
    r = log_returns(df["adjusted_close"]) * 100.0
    if len(r) < window + MIN_FORECASTS:
        raise InsufficientData(company.symbol)

    out = evaluation.rolling_forecasts(r, window=window, refit_every=refit_every, progress=progress)
    start = out["forecast_start"]
    proxies = evaluation.variance_proxies(df)
    dates = r.index[start:]
    payload = {
        "dates": [d.date().isoformat() for d in dates],
        "forecasts": {m: _clean(v) for m, v in out["forecasts"].items()},
        "proxies": {k: _clean(v.reindex(dates).to_numpy()) for k, v in proxies.items()},
        "failures": out["failures"],
        "non_converged": out["non_converged"],
    }
    row = db.scalar(select(VolatilityEvaluation).where(VolatilityEvaluation.company_id == company.id))
    if row is None:
        row = VolatilityEvaluation(company_id=company.id)
        db.add(row)
    row.window, row.refit_every = window, refit_every
    row.data_end, row.n_forecasts = dates[-1].date(), len(dates)
    row.payload = payload
    db.commit()
    db.refresh(row)
    return row


def get_evaluation(db: Session, company: Company, proxy: str) -> EvaluationOut:
    row = db.scalar(select(VolatilityEvaluation).where(VolatilityEvaluation.company_id == company.id))
    if row is None:
        raise EvaluationNotFound(company.symbol)
    if proxy not in evaluation.PROXIES:
        raise InvalidParameter(f"proxy must be one of: {', '.join(evaluation.PROXIES)}")
    try:
        result = evaluation.evaluate(row.payload, proxy=proxy)
    except ValueError as exc:
        raise InvalidParameter(str(exc)) from exc
    return EvaluationOut.model_validate({
        **result,
        "window": row.window,
        "refit_every": row.refit_every,
        "run_at": row.created_at,
        "data_end": row.data_end,
    })
