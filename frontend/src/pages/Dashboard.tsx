import { Link } from "react-router-dom";
import Badge from "../components/ui/Badge";
import { ErrorMessage } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import DataTable, { type Column } from "../components/ui/DataTable";
import Panel from "../components/ui/Panel";
import PriceChange from "../components/ui/PriceChange";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import type { Mover } from "../types/api";
import { formatDate, formatNumber, formatPrice } from "../utils/format";

const MOVER_COLUMNS: Column<Mover>[] = [
  {
    key: "symbol",
    header: "Symbol",
    sortValue: (r) => r.symbol,
    render: (r) => (
      <Link
        to={`/stocks/${encodeURIComponent(r.symbol)}?exchange=${encodeURIComponent(r.exchange)}`}
        className="font-medium text-accent hover:underline"
      >
        {r.symbol}
      </Link>
    ),
  },
  { key: "exchange", header: "Exchange", render: (r) => <span className="text-muted">{r.exchange}</span> },
  { key: "price", header: "Price", align: "right", sortValue: (r) => r.price, render: (r) => formatPrice(r.price, r.currency) },
  { key: "change_pct", header: "Change", align: "right", sortValue: (r) => r.change_pct, render: (r) => <PriceChange value={r.change_pct} /> },
];

export default function Dashboard() {
  const markets = useApi(() => api.getMarkets(), []);
  const status = useApi(() => api.getMarketStatus(), []);
  const movers = useApi(() => api.getMovers(undefined, 5), []);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-serif text-3xl font-medium">Market overview</h1>
        <div className="flex flex-wrap gap-2" aria-label="Exchange status">
          {status.data?.map((s) => (
            <Badge key={s.exchange} tone={s.is_open ? "up" : "neutral"}>
              {s.exchange} {s.is_open ? "open" : "closed"}
            </Badge>
          ))}
        </div>
      </div>

      {markets.error ? (
        <ErrorMessage message={markets.error.message} onRetry={markets.reload} />
      ) : (
        <Ledger className="sm:grid-cols-2">
          {markets.loading && !markets.data
            ? [0, 1].map((i) => <MetricCard key={i} label="Loading" value="" large loading />)
            : markets.data?.map((q) => (
                <MetricCard
                  key={q.symbol}
                  label={q.name}
                  large
                  value={formatNumber(q.price)}
                  note={
                    <span className="flex items-center gap-2">
                      <PriceChange value={q.change_pct} />
                      <span className="text-muted">as of {formatDate(q.as_of)}</span>
                    </span>
                  }
                />
              ))}
        </Ledger>
      )}

      {movers.error ? (
        <ErrorMessage message={movers.error.message} onRetry={movers.reload} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Panel title="Top gainers" flush>
            <DataTable columns={MOVER_COLUMNS} rows={movers.data?.gainers ?? []} rowKey={(r) => `${r.symbol}-${r.exchange}`} loading={movers.loading} empty="No gainers in the latest session." />
          </Panel>
          <Panel title="Top losers" flush>
            <DataTable columns={MOVER_COLUMNS} rows={movers.data?.losers ?? []} rowKey={(r) => `${r.symbol}-${r.exchange}`} loading={movers.loading} empty="No losers in the latest session." />
          </Panel>
        </div>
      )}

      <p className="text-sm text-muted">
        Figures are stored daily closes, not live quotes. Exchanges close at different times, so the latest date can
        differ between markets. StockLens is for analysis and is not financial advice.
      </p>
    </div>
  );
}
