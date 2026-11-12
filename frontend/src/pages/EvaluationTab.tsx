import { useMemo, useState } from "react";
import { Legend, VolatilityChart, type VolSeries } from "../components/charts/RiskCharts";
import { formatP } from "../components/stats/TestResultCard";
import Badge from "../components/ui/Badge";
import DataTable, { type Column } from "../components/ui/DataTable";
import { ErrorMessage, LoadingSpinner } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import Panel from "../components/ui/Panel";
import RangeSelector from "../components/ui/RangeSelector";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import type { DmTest, EvaluationModel, Proxy } from "../types/api";
import { formatDate, formatNumber } from "../utils/format";
import { MODEL_COLORS } from "../utils/models";

const PROXIES: { value: Proxy; label: string }[] = [
  { value: "parkinson", label: "Parkinson range" },
  { value: "garman_klass", label: "Garman-Klass" },
  { value: "squared_return", label: "Squared return" },
];

const PROXY_TEXT: Record<Proxy, string> = {
  parkinson: "The high low range of each day, which carries more information than one return.",
  garman_klass: "Uses the open, high, low and close of each day.",
  squared_return: "The squared close to close return. Unbiased but very noisy.",
};

const Dm = ({ dm, benchmark }: { dm: DmTest | null; benchmark: boolean }) => {
  if (benchmark) return <span className="text-muted">Benchmark</span>;
  if (!dm) return <span className="text-muted">n/a</span>;
  const significant = dm.p_value < 0.05;
  return (
    <span className="flex flex-col items-end gap-1">
      <span className="num">
        {dm.mean_difference > 0 ? "Lower" : "Higher"} loss, t {formatNumber(dm.statistic, 2)}, p {formatP(dm.p_value)}
      </span>
      <Badge tone={significant ? (dm.mean_difference > 0 ? "up" : "down") : "neutral"}>
        {significant ? "Evidence against equal loss" : "Insufficient evidence to reject"}
      </Badge>
    </span>
  );
};

const InSet = ({ yes }: { yes: boolean }) => <Badge tone={yes ? "up" : "down"}>{yes ? "In the set" : "Excluded"}</Badge>;

const fmtCum = (v: number) => formatNumber(v, 1);

export default function EvaluationTab({ symbol, exchange }: { symbol: string; exchange?: string }) {
  const [proxy, setProxy] = useState<Proxy>("parkinson");
  const res = useApi(() => api.getForecastEvaluation(symbol, { proxy, exchange }), [symbol, exchange, proxy]);
  const d = res.data;

  const series: VolSeries[] = useMemo(
    () => (d ? Object.entries(d.cumulative.series).map(([id, v]) => ({
      name: d.models.find((m) => m.id === id)?.name ?? id,
      color: MODEL_COLORS[id],
      points: d.cumulative.dates.map((date, i) => ({ date, value: v[i] })),
    })) : []),
    [d],
  );

  const picker = (
    <RangeSelector label="Realised variance proxy" value={proxy} onChange={setProxy} options={PROXIES} />
  );

  if (res.error?.code === "evaluation_not_found") {
    return (
      <div className="space-y-4">
        <Panel title="No evaluation stored for this stock yet">
          <p className="max-w-prose text-sm text-muted">
            The evaluation re-fits all six models on a rolling window, which takes about a minute, so it runs as a
            batch job and the result is stored. Run this in the backend folder, then reload this page:
          </p>
          <pre className="mt-3 overflow-x-auto rounded border border-rule bg-panel2 p-3 text-sm">
            <code>python -m app.scripts.evaluate --symbols {symbol}</code>
          </pre>
        </Panel>
      </div>
    );
  }
  if (res.error) return <ErrorMessage message={res.error.message} onRetry={res.reload} />;
  if (!d) return <LoadingSpinner label="Loading the stored evaluation" />;

  const benchmarkName = d.models.find((m) => m.id === d.benchmark)?.name ?? d.benchmark;
  const columns: Column<EvaluationModel>[] = [
    {
      key: "name", header: "Model", sortValue: (m) => m.name,
      render: (m) => (
        <span className="flex items-center gap-2">
          <span aria-hidden className="inline-block h-2 w-2 rounded-full" style={{ background: MODEL_COLORS[m.id] }} />
          {m.name}
        </span>
      ),
    },
    { key: "q", header: "Mean QLIKE", align: "right", sortValue: (m) => m.mean_qlike, render: (m) => formatNumber(m.mean_qlike, 4) },
    { key: "qr", header: "QLIKE rank", align: "right", sortValue: (m) => m.rank_qlike, render: (m) => m.rank_qlike },
    { key: "dmq", header: `QLIKE against ${benchmarkName}`, align: "right", render: (m) => <Dm dm={m.dm_qlike} benchmark={m.id === d.benchmark} /> },
    { key: "mq", header: "Confidence set, QLIKE", align: "right", sortValue: (m) => m.mcs_p_qlike, render: (m) => <InSet yes={m.in_mcs_qlike} /> },
    { key: "m", header: "Mean MSE", align: "right", sortValue: (m) => m.mean_mse, render: (m) => formatNumber(m.mean_mse, 2) },
    { key: "mr", header: "MSE rank", align: "right", sortValue: (m) => m.rank_mse, render: (m) => m.rank_mse },
    { key: "mm", header: "Confidence set, MSE", align: "right", sortValue: (m) => m.mcs_p_mse, render: (m) => <InSet yes={m.in_mcs_mse} /> },
    { key: "f", header: "Refit problems", align: "right", sortValue: (m) => m.failures + m.non_converged, render: (m) => m.failures + m.non_converged },
  ];

  const problems = d.models.some((m) => m.failures + m.non_converged > 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        {picker}
        {res.loading && <LoadingSpinner label="Updating" />}
      </div>
      <p className="max-w-prose text-sm text-muted">{PROXY_TEXT[proxy]}</p>

      <Ledger className="grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Forecast days" value={formatNumber(d.observations, 0)} note={<span className="text-muted">One day ahead, out of sample</span>} />
        <MetricCard label="Period" value={`${formatDate(d.first_date)} to ${formatDate(d.last_date)}`} className="col-span-2 lg:col-span-1" />
        <MetricCard label="Estimation window" value={`${d.window} days`} note={<span className="text-muted">Re-fitted every {d.refit_every} days</span>} />
        <MetricCard label="Benchmark" value={benchmarkName} />
      </Ledger>

      <Panel title="Out of sample loss" flush>
        <DataTable columns={columns} rows={d.models} rowKey={(m) => m.id} />
      </Panel>
      <div className="max-w-prose space-y-2 text-sm text-muted">
        <p>
          Lower loss is better. QLIKE punishes forecasts that are too low more than forecasts that are too high, and
          it is the loss most used for volatility. MSE is dominated by a few extreme days, so read the two together.
        </p>
        <p>
          The test against {benchmarkName} is a Diebold Mariano test of equal expected loss. The confidence set keeps
          every model that cannot be told apart from the best at the {Math.round(d.mcs_alpha * 100)}% level. A larger
          set means the data cannot separate the models, which is common in a few years of daily data.
        </p>
      </div>

      <Panel title={`Cumulative QLIKE advantage over ${benchmarkName}`}>
        <VolatilityChart series={series} label={`Cumulative QLIKE loss of ${benchmarkName} minus each model`} height={280} format={fmtCum} />
        <Legend series={series} />
        <p className="mt-3 max-w-prose text-sm text-muted">
          A line that rises means the model has had lower loss than {benchmarkName} over that stretch. A steady slope
          is a consistent edge. A jump on a few days means the result rests on a few events.
        </p>
      </Panel>

      <Panel title="How this was produced">
        <ul className="max-w-prose list-disc space-y-1.5 pl-5 text-sm text-muted">
          <li>Each model is estimated on the previous {d.window} returns and re-estimated every {d.refit_every} trading days. Between re-fits the parameters stay fixed while the variance updates daily, so no forecast uses information from its own day or later.</li>
          <li>
            {proxy === "squared_return"
              ? "The proxy is the squared return, so no rescaling is needed."
              : `Range based proxies miss the overnight gap, so they are multiplied by ${formatNumber(d.scale_factor, 2)} to match the mean squared return over these days.`}
            {d.dropped > 0 && ` ${d.dropped} days with no usable proxy or forecast were left out of every model.`}
          </li>
          <li>Run on {formatDate(d.run_at.slice(0, 10))}, with data to {formatDate(d.data_end)}. Run the batch command again after new prices are loaded.</li>
          {problems && <li>Some re-fits failed or did not converge. A failed re-fit reuses the previous parameters.</li>}
          {d.excluded.length > 0 && <li>Left out because they produced no usable forecasts: {d.excluded.join(", ")}.</li>}
        </ul>
      </Panel>
    </div>
  );
}
