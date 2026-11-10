import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import Badge from "../components/ui/Badge";
import { EmptyState, ErrorMessage, Skeleton } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import Panel from "../components/ui/Panel";
import PriceChange from "../components/ui/PriceChange";
import Tabs, { type TabItem } from "../components/ui/Tabs";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import { currencyLabel, formatCompact, formatDate, formatNumber, formatPrice } from "../utils/format";

const TABS: TabItem[] = [
  { id: "overview", label: "Overview" },
  { id: "performance", label: "Performance", disabled: true },
  { id: "technical", label: "Technical", disabled: true },
  { id: "risk", label: "Risk", disabled: true },
  { id: "statistics", label: "Statistics", disabled: true },
  { id: "forecast", label: "Forecast", disabled: true },
];

export default function Stock() {
  const { symbol = "" } = useParams();
  const [params] = useSearchParams();
  const exchange = params.get("exchange") ?? undefined;
  const [tab, setTab] = useState("overview");

  const profile = useApi(() => api.getProfile(symbol, exchange), [symbol, exchange]);
  const quote = useApi(() => api.getQuote(symbol, exchange), [symbol, exchange]);

  if (profile.error?.code === "stock_not_found") {
    return (
      <EmptyState
        title={`No stock called ${symbol}`}
        action={<Link to="/" className="text-accent hover:underline">Back to the dashboard</Link>}
      >
        Use the search box to find a symbol or company name.
      </EmptyState>
    );
  }
  if (profile.error) return <ErrorMessage message={profile.error.message} onRetry={profile.reload} />;

  const p = profile.data;
  const q = quote.data;
  const isIndex = p?.asset_type === "index";
  const money = (v: number | undefined) => (p && v !== undefined ? formatPrice(v, p.currency, p.asset_type) : "n/a");

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

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <EmptyState title="Price chart comes next">
            {p
              ? `${formatNumber(p.observations, 0)} daily bars from ${formatDate(p.data_start)} to ${formatDate(p.data_end)} are stored and ready to plot.`
              : "Loading data coverage."}
          </EmptyState>
        </div>
        <Panel title="About">
          <dl className="grid grid-cols-[7rem_1fr] gap-x-3 gap-y-2 text-sm">
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
    </div>
  );
}
