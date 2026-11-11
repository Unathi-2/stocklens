"""Database queries and calculations behind the stock endpoints."""
from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from collections import OrderedDict

from app.analytics import performance, risk, statistics, technical, volatility
from app.analytics.returns import log_returns
from app.core.errors import AmbiguousSymbol, InsufficientData, NoPriceData, StockNotFound
from app.models import Company, PriceHistory
from app.schemas.stock import (
    BarOut, DayValueOut, IndicatorOut, MoverOut, PerformanceOut, PerformanceSummaryOut,
    PointOut, ProfileOut, QuoteOut, RiskOut, StatisticsOut, VolatilityModelsOut,
)

PERIOD_DAYS = {"1m": 31, "3m": 92, "6m": 183, "1y": 366, "5y": 1827}
RESAMPLE_RULE = {"1wk": "W-FRI", "1mo": "ME"}


def _resolve_start(latest: date, period: str, start: date | None) -> date | None:
    """An explicit start wins. Otherwise count back from the latest stored date."""
    if start is not None:
        return start
    if period == "max":
        return None
    return latest - timedelta(days=PERIOD_DAYS[period])


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

    start = _resolve_start(latest, period, start)

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
                currency=company.currency,
                as_of=d,
                price=last,
                change_pct=(last - prev) / prev * 100,
            )
        )
    results.sort(key=lambda m: m.change_pct, reverse=True)
    gainers = [m for m in results if m.change_pct > 0][:limit]
    losers = sorted([m for m in results if m.change_pct < 0], key=lambda m: m.change_pct)[:limit]
    return gainers, losers


def get_indicators(
    db: Session,
    company: Company,
    period: str,
    interval: str,
    start: date | None,
    end: date | None,
    sma_windows: list[int],
    ema_windows: list[int],
) -> list[IndicatorOut]:
    """Moving averages are computed on the full history and trimmed afterwards,
    so a 200 day average is already valid on the first day of a 1 year window."""
    full = get_history(db, company, "max", interval)
    closes = pd.Series([b.close for b in full], index=pd.to_datetime([b.date for b in full]))
    lo = _resolve_start(full[-1].date, period, start)

    jobs = [("sma", w, technical.sma(closes, w)) for w in sma_windows]
    jobs += [("ema", w, technical.ema(closes, w)) for w in ema_windows]

    out: list[IndicatorOut] = []
    for kind, window, series in jobs:
        points = [
            PointOut(date=ts.date(), value=float(v))
            for ts, v in series.dropna().items()
            if (lo is None or ts.date() >= lo) and (end is None or ts.date() <= end)
        ]
        out.append(IndicatorOut(name=f"{kind.upper()} {window}", kind=kind, window=window, points=points))
    return out


def get_performance(
    db: Session, company: Company, period: str, start: date | None, end: date | None
) -> PerformanceOut:
    """Daily total return measures. Uses adjusted closes so dividends are included."""
    bars = get_history(db, company, period, "1d", start, end)
    if len(bars) < 3:
        raise InsufficientData(company.symbol)

    prices = pd.Series([b.adjusted_close for b in bars], index=pd.to_datetime([b.date for b in bars]))
    s = performance.summarise(prices)
    cumulative = performance.cumulative_return_pct(prices)
    returns = log_returns(prices) * 100.0

    return PerformanceOut(
        summary=PerformanceSummaryOut(
            start_date=s["start_date"],
            end_date=s["end_date"],
            observations=s["observations"],
            total_return_pct=s["total_return_pct"],
            annualised_volatility_pct=s["annualised_volatility_pct"],
            mean_daily_return_pct=s["mean_daily_return_pct"],
            best_day=DayValueOut(date=s["best_day"][0], value=s["best_day"][1]),
            worst_day=DayValueOut(date=s["worst_day"][0], value=s["worst_day"][1]),
        ),
        cumulative_return=[PointOut(date=ts.date(), value=float(v)) for ts, v in cumulative.items()],
        daily_returns=[PointOut(date=ts.date(), value=float(v)) for ts, v in returns.items()],
    )


def get_statistics(
    db: Session, company: Company, period: str, start: date | None, end: date | None
) -> StatisticsOut:
    """Distribution and time series diagnostics on daily adjusted close log returns."""
    bars = get_history(db, company, period, "1d", start, end)
    if len(bars) < statistics.MIN_OBSERVATIONS + 1:
        raise InsufficientData(company.symbol)
    prices = pd.Series([b.adjusted_close for b in bars], index=pd.to_datetime([b.date for b in bars]))
    return StatisticsOut.model_validate(statistics.analyse(prices))


def _points(series: pd.Series) -> list[PointOut]:
    return [PointOut(date=ts.date(), value=float(v)) for ts, v in series.items()]


def get_risk(
    db: Session, company: Company, period: str, start: date | None, end: date | None, risk_free_pct: float
) -> RiskOut:
    """Drawdown, VaR, ES, ratios, rolling volatility and a GARCH(1,1) fit on daily adjusted closes."""
    bars = get_history(db, company, period, "1d", start, end)
    if len(bars) < risk.MIN_OBSERVATIONS + 1:
        raise InsufficientData(company.symbol)
    prices = pd.Series([b.adjusted_close for b in bars], index=pd.to_datetime([b.date for b in bars]))
    result = risk.analyse(prices, risk_free_pct)

    garch = result["garch"]
    if garch is not None:
        garch = {**garch, "volatility": _points(garch["volatility"])}
    return RiskOut.model_validate(
        {
            **result,
            "drawdown": {**result["drawdown"], "series": _points(result["drawdown"]["series"])},
            "rolling_volatility": [
                {"window": w, "points": _points(s)} for w, s in result["rolling_volatility"].items()
            ],
            "garch": garch,
        }
    )


_VOL_CACHE: "OrderedDict[tuple, VolatilityModelsOut]" = OrderedDict()
_VOL_CACHE_SIZE = 32


def get_volatility_models(
    db: Session, company: Company, period: str, start: date | None, end: date | None
) -> VolatilityModelsOut:
    """Fits six volatility models. Results are cached per stock and window, because the fit takes a few seconds."""
    bars = get_history(db, company, period, "1d", start, end)
    if len(bars) < volatility.MIN_OBSERVATIONS + 1:
        raise InsufficientData(company.symbol)

    key = (company.id, bars[0].date, bars[-1].date, len(bars))
    if key in _VOL_CACHE:
        _VOL_CACHE.move_to_end(key)
        return _VOL_CACHE[key]

    prices = pd.Series([b.adjusted_close for b in bars], index=pd.to_datetime([b.date for b in bars]))
    result = VolatilityModelsOut.model_validate(volatility.analyse(prices))
    _VOL_CACHE[key] = result
    while len(_VOL_CACHE) > _VOL_CACHE_SIZE:
        _VOL_CACHE.popitem(last=False)
    return result
