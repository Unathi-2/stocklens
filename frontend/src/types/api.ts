export interface Envelope<T> {
  data: T;
  meta: Record<string, unknown>;
}

export interface Company {
  symbol: string;
  name: string;
  exchange: string;
  asset_type: string;
  sector: string | null;
  industry: string | null;
  country: string | null;
  currency: string;
  market_cap: number | null;
}

export interface Profile extends Company {
  data_start: string | null;
  data_end: string | null;
  observations: number;
}

export interface Quote {
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  as_of: string;
  price: number;
  previous_close: number | null;
  change: number | null;
  change_pct: number | null;
  open: number;
  high: number;
  low: number;
  volume: number;
  week52_high: number;
  week52_low: number;
}

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adjusted_close: number;
  volume: number;
}

export interface Mover {
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  as_of: string;
  price: number;
  change_pct: number;
}

export interface Movers {
  gainers: Mover[];
  losers: Mover[];
}

export interface ExchangeStatus {
  exchange: string;
  is_open: boolean;
  local_time: string;
  opens: string;
  closes: string;
  note: string;
}

export type Period = "1m" | "3m" | "6m" | "1y" | "5y" | "max";
export type Interval = "1d" | "1wk" | "1mo";

export interface Point {
  date: string;
  value: number;
}

export interface IndicatorSeries {
  name: string;
  kind: "sma" | "ema";
  window: number;
  points: Point[];
}

export interface PerformanceSummary {
  start_date: string;
  end_date: string;
  observations: number;
  total_return_pct: number;
  annualised_volatility_pct: number;
  mean_daily_return_pct: number;
  best_day: Point;
  worst_day: Point;
}

export interface Performance {
  summary: PerformanceSummary;
  cumulative_return: Point[];
  daily_returns: Point[];
}

export interface StatsSummary {
  observations: number;
  mean_pct: number;
  median_pct: number;
  std_pct: number;
  skewness: number;
  excess_kurtosis: number;
  min_pct: number;
  max_pct: number;
}

export interface TestResult {
  id: string;
  name: string;
  applied_to: string;
  null_hypothesis: string;
  statistic: number;
  p_value: number;
  reject_null: boolean;
  alpha: number;
  interpretation: string;
  details: Record<string, number>;
}

export interface Statistics {
  summary: StatsSummary;
  histogram: { bin_centers: number[]; density: number[]; normal_density: number[]; bin_width: number };
  qq: { theoretical: number[]; sample: number[] };
  tests: TestResult[];
  acf: { lags: number[]; returns: number[]; squared_returns: number[]; pacf_returns: number[]; confidence_bound: number };
}

export interface RiskSummary {
  annualised_return_pct: number | null;
  annualised_volatility_pct: number;
  downside_deviation_pct: number;
  sharpe: number | null;
  sortino: number | null;
  calmar: number | null;
  risk_free_pct: number;
}

export interface Drawdown {
  max_drawdown_pct: number;
  peak_date: string | null;
  trough_date: string | null;
  recovery_date: string | null;
  current_drawdown_pct: number;
  longest_underwater_days: number;
  series: Point[];
}

export interface VarRow {
  confidence: number;
  historical_var_pct: number;
  normal_var_pct: number;
  cornish_fisher_var_pct: number;
  historical_es_pct: number;
  normal_es_pct: number;
}

export interface Backtest {
  confidence: number;
  tests: number;
  violations: number;
  expected_violations: number;
  violation_rate_pct: number;
  lr_statistic: number;
  p_value: number;
  reject_null: boolean;
}

export interface GarchParam {
  name: string;
  estimate: number;
  std_error: number | null;
  p_value: number | null;
}

export interface Garch {
  converged: boolean;
  parameters: GarchParam[];
  persistence: number;
  half_life_days: number | null;
  unconditional_volatility_pct: number | null;
  latest_volatility_pct: number;
  log_likelihood: number;
  aic: number;
  bic: number;
  observations: number;
  volatility: Point[];
}

export interface Risk {
  summary: RiskSummary;
  drawdown: Drawdown;
  rolling_volatility: { window: number; points: Point[] }[];
  var: VarRow[];
  backtests: Backtest[];
  garch: Garch | null;
}

export interface VolModel {
  id: string;
  name: string;
  converged: boolean;
  error: string | null;
  n_params: number | null;
  log_likelihood: number | null;
  aic: number | null;
  bic: number | null;
  parameters: GarchParam[];
  persistence: number | null;
  half_life_days: number | null;
  memory_d: number | null;
  mean_volatility_pct: number | null;
  latest_volatility_pct: number | null;
  residual_tests: { ljung_box_p: number; ljung_box_squared_p: number; jarque_bera_p: number } | null;
  volatility: number[];
  forecast: number[];
  news_impact: { shock: number[]; volatility: number[] } | null;
}

export interface VolatilityModels {
  dates: string[];
  observations: number;
  horizon: number;
  forecast_dates: string[];
  realised_21d: (number | null)[];
  models: VolModel[];
  best_aic: string | null;
  best_bic: string | null;
}

export interface DmTest {
  mean_difference: number;
  statistic: number;
  p_value: number;
}

export interface EvaluationModel {
  id: string;
  name: string;
  mean_qlike: number;
  mean_mse: number;
  rank_qlike: number;
  rank_mse: number;
  dm_qlike: DmTest | null;
  dm_mse: DmTest | null;
  mcs_p_qlike: number;
  mcs_p_mse: number;
  in_mcs_qlike: boolean;
  in_mcs_mse: boolean;
  failures: number;
  non_converged: number;
}

export type Proxy = "parkinson" | "garman_klass" | "squared_return";

export interface Evaluation {
  proxy: Proxy;
  scale_factor: number;
  observations: number;
  dropped: number;
  first_date: string;
  last_date: string;
  window: number;
  refit_every: number;
  benchmark: string;
  mcs_alpha: number;
  run_at: string;
  data_end: string;
  models: EvaluationModel[];
  excluded: string[];
  cumulative: { dates: string[]; series: Record<string, number[]> };
}
