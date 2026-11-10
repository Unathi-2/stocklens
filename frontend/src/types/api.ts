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
