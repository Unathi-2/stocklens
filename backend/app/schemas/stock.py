from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: dict = {}


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    exchange: str
    asset_type: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    currency: str
    market_cap: int | None = None


class ProfileOut(CompanyOut):
    data_start: date | None = None
    data_end: date | None = None
    observations: int = 0


class QuoteOut(BaseModel):
    symbol: str
    name: str
    exchange: str
    currency: str
    as_of: date
    price: float
    previous_close: float | None = None
    change: float | None = None
    change_pct: float | None = None
    open: float
    high: float
    low: float
    volume: int
    week52_high: float
    week52_low: float


class BarOut(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int


class MoverOut(BaseModel):
    symbol: str
    name: str
    exchange: str
    currency: str
    as_of: date
    price: float
    change_pct: float


class MoversOut(BaseModel):
    gainers: list[MoverOut]
    losers: list[MoverOut]


class ExchangeStatusOut(BaseModel):
    exchange: str
    is_open: bool
    local_time: str
    opens: str
    closes: str
    note: str


class PointOut(BaseModel):
    date: date
    value: float


class IndicatorOut(BaseModel):
    name: str
    kind: Literal["sma", "ema"]
    window: int
    points: list[PointOut]


class DayValueOut(BaseModel):
    date: date
    value: float


class PerformanceSummaryOut(BaseModel):
    start_date: date
    end_date: date
    observations: int
    total_return_pct: float
    annualised_volatility_pct: float
    mean_daily_return_pct: float
    best_day: DayValueOut
    worst_day: DayValueOut


class PerformanceOut(BaseModel):
    summary: PerformanceSummaryOut
    cumulative_return: list[PointOut]
    daily_returns: list[PointOut]


class StatsSummaryOut(BaseModel):
    observations: int
    mean_pct: float
    median_pct: float
    std_pct: float
    skewness: float
    excess_kurtosis: float
    min_pct: float
    max_pct: float


class HistogramOut(BaseModel):
    bin_centers: list[float]
    density: list[float]
    normal_density: list[float]
    bin_width: float


class QQOut(BaseModel):
    theoretical: list[float]
    sample: list[float]


class TestResultOut(BaseModel):
    id: str
    name: str
    applied_to: str
    null_hypothesis: str
    statistic: float
    p_value: float
    reject_null: bool
    alpha: float
    interpretation: str
    details: dict[str, float | int]


class CorrelogramOut(BaseModel):
    lags: list[int]
    returns: list[float]
    squared_returns: list[float]
    pacf_returns: list[float]
    confidence_bound: float


class StatisticsOut(BaseModel):
    summary: StatsSummaryOut
    histogram: HistogramOut
    qq: QQOut
    tests: list[TestResultOut]
    acf: CorrelogramOut


class RiskSummaryOut(BaseModel):
    annualised_return_pct: float | None
    annualised_volatility_pct: float
    downside_deviation_pct: float
    sharpe: float | None
    sortino: float | None
    calmar: float | None
    risk_free_pct: float


class DrawdownOut(BaseModel):
    max_drawdown_pct: float
    peak_date: date | None
    trough_date: date | None
    recovery_date: date | None
    current_drawdown_pct: float
    longest_underwater_days: int
    series: list[PointOut]


class RollingVolOut(BaseModel):
    window: int
    points: list[PointOut]


class VarRowOut(BaseModel):
    confidence: float
    historical_var_pct: float
    normal_var_pct: float
    cornish_fisher_var_pct: float
    historical_es_pct: float
    normal_es_pct: float


class BacktestOut(BaseModel):
    confidence: float
    tests: int
    violations: int
    expected_violations: float
    violation_rate_pct: float
    lr_statistic: float
    p_value: float
    reject_null: bool


class GarchParamOut(BaseModel):
    name: str
    estimate: float
    std_error: float | None
    p_value: float | None


class GarchOut(BaseModel):
    converged: bool
    parameters: list[GarchParamOut]
    persistence: float
    half_life_days: float | None
    unconditional_volatility_pct: float | None
    latest_volatility_pct: float
    log_likelihood: float
    aic: float
    bic: float
    observations: int
    volatility: list[PointOut]


class RiskOut(BaseModel):
    summary: RiskSummaryOut
    drawdown: DrawdownOut
    rolling_volatility: list[RollingVolOut]
    var: list[VarRowOut]
    backtests: list[BacktestOut]
    garch: GarchOut | None


class ResidualTestsOut(BaseModel):
    ljung_box_p: float
    ljung_box_squared_p: float
    jarque_bera_p: float


class NewsImpactOut(BaseModel):
    shock: list[float]
    volatility: list[float]


class VolModelOut(BaseModel):
    id: str
    name: str
    converged: bool
    error: str | None
    n_params: int | None
    log_likelihood: float | None
    aic: float | None
    bic: float | None
    parameters: list[GarchParamOut]
    persistence: float | None
    half_life_days: float | None
    memory_d: float | None
    mean_volatility_pct: float | None
    latest_volatility_pct: float | None
    residual_tests: ResidualTestsOut | None
    volatility: list[float]
    forecast: list[float]
    news_impact: NewsImpactOut | None


class VolatilityModelsOut(BaseModel):
    dates: list[date]
    observations: int
    horizon: int
    forecast_dates: list[date]
    realised_21d: list[float | None]
    models: list[VolModelOut]
    best_aic: str | None
    best_bic: str | None


class DmOut(BaseModel):
    mean_difference: float
    statistic: float
    p_value: float


class EvaluationModelOut(BaseModel):
    id: str
    name: str
    mean_qlike: float
    mean_mse: float
    rank_qlike: int
    rank_mse: int
    dm_qlike: DmOut | None
    dm_mse: DmOut | None
    mcs_p_qlike: float
    mcs_p_mse: float
    in_mcs_qlike: bool
    in_mcs_mse: bool
    failures: int
    non_converged: int


class CumulativeOut(BaseModel):
    dates: list[date]
    series: dict[str, list[float]]


class EvaluationOut(BaseModel):
    proxy: str
    scale_factor: float
    observations: int
    dropped: int
    first_date: date
    last_date: date
    window: int
    refit_every: int
    benchmark: str
    mcs_alpha: float
    run_at: datetime
    data_end: date
    models: list[EvaluationModelOut]
    excluded: list[str]
    cumulative: CumulativeOut
