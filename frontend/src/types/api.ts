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
