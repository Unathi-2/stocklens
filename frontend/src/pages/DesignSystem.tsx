import { useState } from "react";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import DataTable, { type Column } from "../components/ui/DataTable";
import { EmptyState, ErrorMessage, LoadingSpinner, Skeleton } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import Panel from "../components/ui/Panel";
import PriceChange from "../components/ui/PriceChange";
import RangeSelector from "../components/ui/RangeSelector";
import Select from "../components/ui/Select";
import StockCard from "../components/ui/StockCard";
import Tabs from "../components/ui/Tabs";
import type { Period } from "../types/api";

const SWATCHES = [
  ["bg", "Page"], ["panel", "Panel"], ["panel2", "Raised"], ["rule", "Rule"],
  ["accent", "Accent"], ["up", "Gain"], ["down", "Loss"], ["muted", "Muted text"],
];

interface Row { symbol: string; price: number; change: number }
const ROWS: Row[] = [
  { symbol: "NPN", price: 142350.5, change: 1.82 },
  { symbol: "SBK", price: 31655, change: -0.64 },
  { symbol: "AAPL", price: 350.69, change: 0 },
];
const COLS: Column<Row>[] = [
  { key: "symbol", header: "Symbol", sortValue: (r) => r.symbol },
  { key: "price", header: "Price", align: "right", sortValue: (r) => r.price, render: (r) => r.price.toFixed(2) },
  { key: "change", header: "Change", align: "right", sortValue: (r) => r.change, render: (r) => <PriceChange value={r.change} /> },
];

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="font-serif text-xl">{title}</h2>
      {children}
    </section>
  );
}

export default function DesignSystem() {
  const [tab, setTab] = useState("a");
  const [period, setPeriod] = useState<Period>("1y");

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-serif text-3xl font-medium">Design system</h1>
        <p className="mt-2 max-w-prose text-muted">
          Every shared component in one place. Colours are semantic tokens that change with the theme, so switch
          themes with the sun or moon button to check both.
        </p>
      </div>

      <Block title="Colour">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {SWATCHES.map(([token, label]) => (
            <div key={token} className="rounded-md border border-rule p-2">
              <div className="h-10 rounded border border-rule" style={{ background: `var(--${token})` }} />
              <div className="mt-2 text-sm">{label}</div>
              <div className="text-xs text-muted">--{token}</div>
            </div>
          ))}
        </div>
      </Block>

      <Block title="Type">
        <div className="space-y-2">
          <div className="font-serif text-4xl">Serif for titles and large figures</div>
          <div className="figure text-3xl">1,234,567.89</div>
          <p className="max-w-prose">Plex Sans carries body text and table figures. <span className="num">1,234,567.89</span> uses tabular figures so columns align.</p>
          <p className="text-sm text-muted">Small supporting text uses the muted colour.</p>
        </div>
      </Block>

      <Block title="Buttons and badges">
        <div className="flex flex-wrap items-center gap-3">
          <Button variant="primary">Run model</Button>
          <Button>Export data</Button>
          <Button variant="ghost">Cancel</Button>
          <Button disabled>Unavailable</Button>
          <Badge>JSE</Badge><Badge tone="accent">NPN</Badge><Badge tone="up">Open</Badge><Badge tone="down">Closed</Badge>
        </div>
      </Block>

      <Block title="Figures">
        <Ledger className="sm:grid-cols-3">
          <MetricCard label="FTSE/JSE All Share" large value="108,421.30" note={<PriceChange value={0.42} />} />
          <MetricCard label="S&P 500" large value="6,643.92" note={<PriceChange value={-0.31} />} />
          <MetricCard label="Annual volatility" value="23.41%" note={<span className="text-muted">Historical, 252 days</span>} />
        </Ledger>
      </Block>

      <Block title="Controls">
        <div className="flex flex-wrap items-end gap-4">
          <RangeSelector
            label="Date range"
            value={period}
            onChange={setPeriod}
            options={[{ value: "1m", label: "1M" }, { value: "3m", label: "3M" }, { value: "1y", label: "1Y" }, { value: "5y", label: "5Y" }, { value: "max", label: "Max" }]}
          />
          <Select label="Model" options={[{ value: "garch", label: "GARCH" }, { value: "egarch", label: "EGARCH" }]} />
        </div>
        <Tabs label="Example tabs" value={tab} onChange={setTab} tabs={[{ id: "a", label: "Overview" }, { id: "b", label: "Risk" }, { id: "c", label: "Forecast", disabled: true }]} />
      </Block>

      <Block title="Table">
        <Panel flush><DataTable columns={COLS} rows={ROWS} rowKey={(r) => r.symbol} /></Panel>
      </Block>

      <Block title="Stock card">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StockCard symbol="NPN" name="Naspers" exchange="JSE" currency="ZAc" price={142350.5} changePct={1.82} />
          <StockCard symbol="AAPL" name="Apple Inc." exchange="NASDAQ" currency="USD" price={350.69} changePct={-2.43} />
        </div>
      </Block>

      <Block title="Loading, error and empty states">
        <div className="space-y-4">
          <div className="flex items-center gap-6"><LoadingSpinner label="Loading prices" /><Skeleton className="h-6 w-40" /></div>
          <ErrorMessage message="Cannot reach the API. Check that the backend is running." onRetry={() => {}} />
          <EmptyState title="Your watchlist is empty">Search for a stock and add it to follow its price here.</EmptyState>
        </div>
      </Block>
    </div>
  );
}
