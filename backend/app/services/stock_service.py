"""Database queries and calculations behind the stock endpoints."""
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AmbiguousSymbol, NoPriceData, StockNotFound
from app.models import Company, PriceHistory
from app.schemas.stock import BarOut, MoverOut, ProfileOut, QuoteOut

PERIOD_DAYS = {"1m": 31, "3m": 92, "6m": 183, "1y": 366, "5y": 1827}
RESAMPLE_RULE = {"1wk": "W-FRI", "1mo": "ME"}


def find_company(db: Session, symbol: str, exchange: str | None = None) -> Company:
    query = select(Company).where(func.upper(Company.symbol) == symbol.upper())
    if exchange:
        query = query.where(func.upper(Company.exchange) == exchange.upper())
    rows = list(db.scalars(query))
    if not rows:
        raise StockNotFound(symbol)
    if len(rows) > 1:
        raise AmbiguousSymbol(symbol, sorted(c.exchange for c in rows))
    return rows[0]


def search_companies(db: Session, q: str, limit: int = 10) -> list[Company]:
    like = f"%{q.strip().lower()}%"
    query = (
        select(Company)
        .where(func.lower(Company.symbol).like(like) | func.lower(Company.name).like(like))
        .order_by(Company.symbol)
        .limit(limit)
    )
    return list(db.scalars(query))


def build_quote(db: Session, company: Company) -> QuoteOut:
    bars = list(
        db.scalars(
            select(PriceHistory)
            .where(PriceHistory.company_id == company.id)
            .order_by(PriceHistory.date.desc())
            .limit(2)
        )
    )
    if not bars:
        raise NoPriceData(company.symbol)
    last = bars[0]
    prev = bars[1] if len(bars) > 1 else None

    hi, lo = db.execute(
        select(func.max(PriceHistory.high), func.min(PriceHistory.low)).where(
            PriceHistory.company_id == company.id,
            PriceHistory.date >= last.date - timedelta(days=365),
        )
    ).one()

    change = change_pct = prev_close = None
    if prev is not None:
        prev_close = float(prev.close)
        change = float(last.close) - prev_close
        change_pct = change / prev_close * 100

    return QuoteOut(
        symbol=company.symbol,
        name=company.name,
        exchange=company.exchange,
        currency=company.currency,
        as_of=last.date,
        price=float(last.close),
        previous_close=prev_close,
        change=change,
        change_pct=change_pct,
        open=float(last.open),
        high=float(last.high),
        low=float(last.low),
        volume=int(last.volume),
        week52_high=float(hi),
        week52_low=float(lo),
    )


def build_profile(db: Session, company: Company) -> ProfileOut:
    start, end, n = db.execute(
        select(func.min(PriceHistory.date), func.max(PriceHistory.date), func.count()).where(
            PriceHistory.company_id == company.id
        )
    ).one()
    base = ProfileOut.model_validate(company)
    return base.model_copy(update={"data_start": start, "data_end": end, "observations": n})


def get_history(
    db: Session,
    company: Company,
    period: str = "1y",
    interval: str = "1d",
    start: date | None = None,
    end: date | None = None,
) -> list[BarOut]:
    latest = db.scalar(select(func.max(PriceHistory.date)).where(PriceHistory.company_id == company.id))
    if latest is None:
        raise NoPriceData(company.symbol)

    if start is None and period != "max":
        start = latest - timedelta(days=PERIOD_DAYS[period])

    query = select(PriceHistory).where(PriceHistory.company_id == company.id)
    if start:
        query = query.where(PriceHistory.date >= start)
    if end:
        query = query.where(PriceHistory.date <= end)
    rows = list(db.scalars(query.order_by(PriceHistory.date)))

    bars = [
        BarOut(
            date=r.date,
            open=float(r.open),
            high=float(r.high),
            low=float(r.low),
            close=float(r.close),
            adjusted_close=float(r.adjusted_close),
            volume=int(r.volume),
        )
        for r in rows
    ]
    if interval == "1d" or not bars:
        return bars
    return _resample(bars, RESAMPLE_RULE[interval])


def _resample(bars: list[BarOut], rule: str) -> list[BarOut]:
    df = pd.DataFrame([b.model_dump() for b in bars])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date", drop=False)
    grouped = df.groupby(pd.Grouper(freq=rule)).agg(
        last_date=("date", "max"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        adjusted_close=("adjusted_close", "last"),
        volume=("volume", "sum"),
    )
    grouped = grouped.dropna(subset=["close"])
    return [
        BarOut(
            date=row.last_date.date(),
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=int(row.volume),
        )
        for row in grouped.itertuples()
    ]


def index_quotes(db: Session) -> list[QuoteOut]:
    indices = db.scalars(select(Company).where(Company.asset_type == "index").order_by(Company.exchange))
    quotes = []
    for company in indices:
        try:
            quotes.append(build_quote(db, company))
        except NoPriceData:
            continue
    return quotes


def movers(db: Session, exchange: str | None = None, limit: int = 5) -> tuple[list[MoverOut], list[MoverOut]]:
    rn = (
        func.row_number()
        .over(partition_by=PriceHistory.company_id, order_by=PriceHistory.date.desc())
        .label("rn")
    )
    sub = select(PriceHistory.company_id, PriceHistory.date, PriceHistory.close, rn).subquery()
    rows = db.execute(
        select(sub.c.company_id, sub.c.date, sub.c.close, sub.c.rn).where(sub.c.rn <= 2)
    ).all()

    by_company: dict[int, dict[int, tuple]] = {}
    for company_id, d, close, n in rows:
        by_company.setdefault(company_id, {})[n] = (d, float(close))

    query = select(Company).where(Company.asset_type == "equity")
    if exchange:
        query = query.where(func.upper(Company.exchange) == exchange.upper())

    results: list[MoverOut] = []
    for company in db.scalars(query):
        pair = by_company.get(company.id, {})
        if 1 not in pair or 2 not in pair:
            continue
        (d, last), (_, prev) = pair[1], pair[2]
        results.append(
            MoverOut(
                symbol=company.symbol,
                name=company.name,
                exchange=company.exchange,
                as_of=d,
                price=last,
                change_pct=(last - prev) / prev * 100,
            )
        )
    results.sort(key=lambda m: m.change_pct, reverse=True)
    gainers = [m for m in results if m.change_pct > 0][:limit]
    losers = sorted([m for m in results if m.change_pct < 0], key=lambda m: m.change_pct)[:limit]
    return gainers, losers
