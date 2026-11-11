import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import PriceChart from "../components/charts/PriceChart";
import SeriesChart from "../components/charts/SeriesChart";
import { INDICATOR_COLORS } from "../components/charts/chartTheme";
import Badge from "../components/ui/Badge";
import { EmptyState, ErrorMessage, LoadingSpinner, Skeleton } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import Panel from "../components/ui/Panel";
import PriceChange from "../components/ui/PriceChange";
import RangeSelector from "../components/ui/RangeSelector";
import Select from "../components/ui/Select";
import Tabs, { type TabItem } from "../components/ui/Tabs";
import Toggle from "../components/ui/Toggle";
import RiskTab from "./RiskTab";
import StatisticsTab from "./StatisticsTab";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import type { Interval, Period } from "../types/api";
import { currencyLabel, formatCompact, formatDate, formatNumber, formatPct, formatPrice } from "../utils/format";

const TABS: TabItem[] = [
  { id: "overview", label: "Overview" },
  { id: "performance", label: "Performance" },
  { id: "technical", label: "Technical", disabled: true },
  { id: "risk", label: "Risk" },
  { id: "statistics", label: "Statistics" },
  { id: "forecast", label: "Forecast", disabled: true },
];

const PERIODS: { value: Period; label: string }[] = [
  { value: "1m", label: "1M" },
  { value: "3m", label: "3M" },
  { value: "6m", label: "6M" },
  { value: "1y", label: "1Y" },
  { value: "5y", label: "5Y" },
  { value: "max", label: "Max" },
];

const INTERVALS = [
  { value: "1d", label: "Daily" },
  { value: "1wk", label: "Weekly" },
  { value: "1mo", label: "Monthly" },
];

const INDICATORS = [
  { key: "sma20", label: "SMA 20" },
  { key: "sma50", label: "SMA 50" },
  { key: "sma200", label: "SMA 200" },
  { key: "ema20", label: "EMA 20" },
];

export default function Stock() {
  const { symbol = "" } = useParams();
  const [params] = useSearchParams();
  const exchange = params.get("exchange") ?? undefined;

  const [tab, setTab] = useState("overview");
  const [period, setPeriod] = useState<Period>("1y");
  const [interval, setInterval] = useState<Interval>("1d");
  const [kind, setKind] = useState<"line" | "candles">("line");
  const [showVolume, setShowVolume] = useState(true);
  const [visible, setVisible] = useState<Record<string, boolean>>({ sma20: true, sma50: true, sma200: false, ema20: false });

  const profile = useApi(() => api.getProfile(symbol, exchange), [symbol, exchange]);
  const quote = useApi(() => api.getQuote(symbol, exchange), [symbol, exchange]);
  const history = useApi(() => api.getHistory(symbol, { period, interval, exchange }), [symbol, exchange, period, interval]);
  const indicators = useApi(
    () => api.getIndicators(symbol, { period, interval, sma: "20,50,200", ema: "20", exchange }),
    [symbol, exchange, period, interval],
  );
  const performance = useApi(() => api.getPerformance(symbol, { period, exchange }), [symbol, exchange, period]);

  if (profile.error?.code === "stock_not_found") {
    return (
      <EmptyState title={`No stock called ${symbol}`} action={<Link to="/" className="text-accent hover:underline">Back to the dashboard</Link>}>
        Use the search box to find a symbol or company name.
      </EmptyState>
    );
  }
  if (profile.error) return <ErrorMessage message={profile.error.message} onRetry={profile.reload} />;

  const p = profile.data;
  const q = quote.data;
  const isIndex = p?.asset_type === "index";
  const money = (v: number | undefined) => (p && v !== undefined ? formatPrice(v, p.currency, p.asset_type) : "n/a");
  const perf = performance.data?.summary;
  const periodControl = <RangeSelector label="Date range" options={PERIODS} value={period} onChange={setPeriod} />;

  return (
    <div className="space-y-6">
      <header>
        {p ? (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="accent">{p.symbol}</Badge>
              <Badge>{p.exchange}</Badge>
              <Badge>{isIndex ? "Index points" : currencyLabel(p.currency)}</Badge>
            </div>
            <h1 className="mt-2 font-serif text-3xl font-medium">{p.name}</h1>
          </>
        ) : (
          <>
            <Skeleton className="h-6 w-40" />
            <Skeleton className="mt-3 h-9 w-72" />
          </>
        )}
        <div className="mt-3 flex flex-wrap items-baseline gap-4">
          {q ? (
            <>
              <span className="figure text-4xl">{money(q.price)}</span>
              <PriceChange value={q.change_pct} className="text-lg" />
              <span className="text-sm text-muted">Close on {formatDate(q.as_of)}</span>
            </>
          ) : quote.error ? (
            <span className="text-sm text-muted">{quote.error.message}</span>
          ) : (
            <Skeleton className="h-10 w-48" />
          )}
        </div>
      </header>

      <Ledger className="grid-cols-2 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard label="Open" value={money(q?.open)} loading={!q && !quote.error} />
        <MetricCard label="High" value={money(q?.high)} loading={!q && !quote.error} />
        <MetricCard label="Low" value={money(q?.low)} loading={!q && !quote.error} />
        <MetricCard label="Volume" value={q ? formatCompact(q.volume) : "n/a"} loading={!q && !quote.error} />
        <MetricCard label="52 week high" value={money(q?.week52_high)} loading={!q && !quote.error} />
        <MetricCard label="52 week low" value={money(q?.week52_low)} loading={!q && !quote.error} />
      </Ledger>

      <Tabs tabs={TABS} value={tab} onChange={setTab} label="Stock sections" />

      {tab === "overview" && (
        <div className="space-y-6">
          <Panel flush>
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-rule px-4 py-3">
              {periodControl}
              <div className="flex flex-wrap items-end gap-3">
                <Select label="Interval" value={interval} onChange={(e) => setInterval(e.target.value as Interval)} options={INTERVALS} />
                <RangeSelector
                  label="Chart type"
                  value={kind}
                  onChange={setKind}
                  options={[{ value: "line", label: "Line" }, { value: "candles", label: "Candles" }]}
                />
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 border-b border-rule px-4 py-2">
              {INDICATORS.map((i) => (
                <Toggle key={i.key} swatch={INDICATOR_COLORS[i.key]} pressed={!!visible[i.key]} onChange={(on) => setVisible((v) => ({ ...v, [i.key]: on }))}>
                  {i.label}
                </Toggle>
              ))}
              <Toggle pressed={showVolume} onChange={setShowVolume}>Volume</Toggle>
              {(history.loading || indicators.loading) && history.data && <LoadingSpinner label="Updating" />}
            </div>
            {history.error ? (
              <div className="p-4"><ErrorMessage message={history.error.message} onRetry={history.reload} /></div>
            ) : history.data && p ? (
              <PriceChart
                bars={history.data}
                indicators={indicators.data ?? []}
                visible={visible}
                kind={kind}
                showVolume={showVolume}
                currency={p.currency}
                assetType={p.asset_type}
              />
            ) : (
              <div className="p-4"><Skeleton className="h-[420px] w-full" /></div>
            )}
          </Panel>
          {indicators.error && <ErrorMessage message={`Moving averages: ${indicators.error.message}`} onRetry={indicators.reload} />}

          <Panel title="About">
            <dl className="grid grid-cols-[7rem_1fr] gap-x-3 gap-y-2 text-sm sm:grid-cols-[7rem_1fr_7rem_1fr]">
              <dt className="text-muted">Sector</dt><dd>{p?.sector ?? "n/a"}</dd>
              <dt className="text-muted">Industry</dt><dd>{p?.industry ?? "n/a"}</dd>
              <dt className="text-muted">Country</dt><dd>{p?.country ?? "n/a"}</dd>
              <dt className="text-muted">Market cap</dt>
              <dd className="num">{p?.market_cap ? `${currencyLabel(p.currency)} ${formatCompact(p.market_cap)}` : "n/a"}</dd>
              <dt className="text-muted">Data from</dt><dd>{formatDate(p?.data_start)}</dd>
              <dt className="text-muted">Data to</dt><dd>{formatDate(p?.data_end)}</dd>
            </dl>
          </Panel>
        </div>
      )}

      {tab === "risk" && (
        <RiskTab symbol={symbol} exchange={exchange} period={period} periodControl={periodControl} />
      )}

      {tab === "statistics" && (
        <StatisticsTab symbol={symbol} exchange={exchange} period={period} periodControl={periodControl} />
      )}

      {tab === "performance" && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            {periodControl}
            {performance.loading && performance.data && <LoadingSpinner label="Updating" />}
          </div>

          {performance.error ? (
            <ErrorMessage message={performance.error.message} onRetry={performance.reload} />
          ) : (
            <>
              <Ledger className="grid-cols-2 lg:grid-cols-5">
                <MetricCard label="Total return" value={perf ? formatPct(perf.total_return_pct) : "n/a"} loading={!perf} />
                <MetricCard label="Annualised volatility" value={perf ? `${formatNumber(perf.annualised_volatility_pct)}%` : "n/a"} loading={!perf} />
                <MetricCard label="Average daily return" value={perf ? formatPct(perf.mean_daily_return_pct, 3) : "n/a"} loading={!perf} />
                <MetricCard
                  label="Best day"
                  value={perf ? formatPct(perf.best_day.value) : "n/a"}
                  note={perf && <span className="text-muted">{formatDate(perf.best_day.date)}</span>}
                  loading={!perf}
                />
                <MetricCard
                  className="col-span-2 lg:col-span-1"
                  label="Worst day"
                  value={perf ? formatPct(perf.worst_day.value) : "n/a"}
                  note={perf && <span className="text-muted">{formatDate(perf.worst_day.date)}</span>}
                  loading={!perf}
                />
              </Ledger>

              <Panel title="Cumulative return" flush>
                {performance.data ? (
                  <SeriesChart points={performance.data.cumulative_return} kind="area" label="Cumulative return in percent" />
                ) : (
                  <div className="p-4"><Skeleton className="h-[260px] w-full" /></div>
                )}
              </Panel>
              <Panel title="Daily log returns" flush>
                {performance.data ? (
                  <SeriesChart points={performance.data.daily_returns} kind="bars" label="Daily log returns in percent" />
                ) : (
                  <div className="p-4"><Skeleton className="h-[260px] w-full" /></div>
                )}
              </Panel>

              <p className="max-w-prose text-sm text-muted">
                Returns use adjusted closes, so dividends are included. Daily returns are log returns, ln(P
                <sub>t</sub> / P<sub>t-1</sub>). Annualised volatility is the standard deviation of daily log returns
                multiplied by the square root of 252. It describes the past and does not predict the future.
                {perf && ` Based on ${perf.observations} trading days from ${formatDate(perf.start_date)} to ${formatDate(perf.end_date)}.`}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
