import type {
  Bar, Company, Envelope, ExchangeStatus, IndicatorSeries, Interval, Movers, Performance, Period, Profile, Quote, Risk, Statistics, VolatilityModels, Evaluation, Proxy,
} from "../types/api";
import { API_BASE } from "./base";

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

type Params = Record<string, string | number | undefined>;

async function request<T>(path: string, params: Params = {}): Promise<Envelope<T>> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") qs.set(key, String(value));
  }
  const query = qs.toString();
  const url = API_BASE + (query ? `${path}?${query}` : path);

  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new ApiError("network_error", "Cannot reach the API. Check that the backend is running.", 0);
  }

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = body?.error;
    if (!err && res.status >= 500) {
      throw new ApiError("api_unavailable", "The API did not respond. Check that the backend and database are running.", res.status);
    }
    const fallback = res.status === 422 ? "The request was not valid." : res.statusText || "Request failed.";
    throw new ApiError(err?.code ?? "http_error", err?.message ?? fallback, res.status);
  }
  return { data: body.data as T, meta: body.meta ?? {} };
}

const stock = (symbol: string) => `/api/v1/stocks/${encodeURIComponent(symbol)}`;

export const api = {
  searchStocks: (q: string, limit = 8) => request<Company[]>("/api/v1/stocks/search", { q, limit }),
  getProfile: (symbol: string, exchange?: string) => request<Profile>(`${stock(symbol)}/profile`, { exchange }),
  getQuote: (symbol: string, exchange?: string) => request<Quote>(`${stock(symbol)}/quote`, { exchange }),
  getHistory: (symbol: string, opts: { period?: Period; interval?: Interval; exchange?: string } = {}) =>
    request<Bar[]>(`${stock(symbol)}/history`, opts),
  getIndicators: (
    symbol: string,
    opts: { period?: Period; interval?: Interval; sma?: string; ema?: string; exchange?: string } = {},
  ) => request<IndicatorSeries[]>(`${stock(symbol)}/indicators`, opts),
  getPerformance: (symbol: string, opts: { period?: Period; exchange?: string } = {}) =>
    request<Performance>(`${stock(symbol)}/performance`, opts),
  getStatistics: (symbol: string, opts: { period?: Period; exchange?: string } = {}) =>
    request<Statistics>(`${stock(symbol)}/statistics`, opts),
  getRisk: (symbol: string, opts: { period?: Period; risk_free?: number; exchange?: string } = {}) =>
    request<Risk>(`${stock(symbol)}/risk`, opts),
  getVolatilityModels: (symbol: string, opts: { period?: Period; exchange?: string } = {}) =>
    request<VolatilityModels>(`${stock(symbol)}/volatility-models`, opts),
  getForecastEvaluation: (symbol: string, opts: { proxy?: Proxy; exchange?: string } = {}) =>
    request<Evaluation>(`${stock(symbol)}/forecast-evaluation`, opts),
  getMarkets: () => request<Quote[]>("/api/v1/markets"),
  getMarketStatus: () => request<ExchangeStatus[]>("/api/v1/markets/status"),
  getMovers: (exchange?: string, limit = 5) => request<Movers>("/api/v1/markets/movers", { exchange, limit }),
};
