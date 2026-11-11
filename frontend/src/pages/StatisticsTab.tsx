import type { ReactNode } from "react";
import { CorrelogramChart, Histogram, QQPlot } from "../components/charts/DiagnosticCharts";
import { ErrorMessage, LoadingSpinner, Skeleton } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import Panel from "../components/ui/Panel";
import TestResultCard from "../components/stats/TestResultCard";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import type { Period } from "../types/api";
import { formatNumber, formatPct } from "../utils/format";

interface Props {
  symbol: string;
  exchange?: string;
  period: Period;
  periodControl: ReactNode;
}

/** Mounted only while the tab is open, so the heavier request runs on demand. */
export default function StatisticsTab({ symbol, exchange, period, periodControl }: Props) {
  const stats = useApi(() => api.getStatistics(symbol, { period, exchange }), [symbol, exchange, period]);
  const d = stats.data;
  const s = d?.summary;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {periodControl}
        {stats.loading && d && <LoadingSpinner label="Updating" />}
      </div>

      {stats.error ? (
        <ErrorMessage message={stats.error.message} onRetry={stats.reload} />
      ) : !d || !s ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-[300px] w-full" />
        </div>
      ) : (
        <>
          <Ledger className="grid-cols-2 lg:grid-cols-5">
            <MetricCard label="Observations" value={formatNumber(s.observations, 0)} />
            <MetricCard label="Mean daily return" value={formatPct(s.mean_pct, 3)} />
            <MetricCard label="Standard deviation" value={`${formatNumber(s.std_pct, 3)}%`} />
            <MetricCard label="Skewness" value={formatNumber(s.skewness, 3)} note={<span className="text-muted">Normal is 0</span>} />
            <MetricCard className="col-span-2 lg:col-span-1" label="Excess kurtosis" value={formatNumber(s.excess_kurtosis, 3)} note={<span className="text-muted">Normal is 0</span>} />
          </Ledger>

          <Panel title="Return distribution">
            <div className="grid gap-6 lg:grid-cols-2">
              <Histogram centers={d.histogram.bin_centers} density={d.histogram.density} normal={d.histogram.normal_density} binWidth={d.histogram.bin_width} />
              <QQPlot theoretical={d.qq.theoretical} sample={d.qq.sample} />
            </div>
            <p className="mt-4 max-w-prose text-sm text-muted">
              Bars taller than the dashed curve at the centre and points that curl away from the line at the ends
              point to fat tails: large moves happen more often than a normal distribution allows.
            </p>
          </Panel>

          <section aria-labelledby="tests-heading" className="space-y-3">
            <h2 id="tests-heading" className="font-serif text-xl">Statistical tests</h2>
            <div className="grid gap-4 lg:grid-cols-2">
              {d.tests.map((t) => <TestResultCard key={t.id} test={t} />)}
            </div>
            <p className="max-w-prose text-sm text-muted">
              All tests use a 5% significance level. A small p value is evidence against the null hypothesis. A large
              one means the data do not contradict it, which is not proof that it is true. Results describe this
              window only and six tests are shown together, so treat a single borderline p value with caution.
            </p>
          </section>

          <Panel title="Autocorrelation">
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <h3 className="mb-1 text-sm font-medium">Returns (ACF)</h3>
                <CorrelogramChart lags={d.acf.lags} values={d.acf.returns} bound={d.acf.confidence_bound} label="Autocorrelation of daily log returns" />
              </div>
              <div>
                <h3 className="mb-1 text-sm font-medium">Squared returns (ACF)</h3>
                <CorrelogramChart lags={d.acf.lags} values={d.acf.squared_returns} bound={d.acf.confidence_bound} label="Autocorrelation of squared daily log returns" />
              </div>
              <div>
                <h3 className="mb-1 text-sm font-medium">Returns (PACF)</h3>
                <CorrelogramChart lags={d.acf.lags} values={d.acf.pacf_returns} bound={d.acf.confidence_bound} label="Partial autocorrelation of daily log returns" />
              </div>
              <div className="text-sm text-muted">
                <h3 className="mb-1 font-medium text-ink">How to read these</h3>
                <p>
                  Bars outside the dashed band (an approximate 95% interval of plus or minus 1.96 divided by the
                  square root of n) differ from zero. Returns usually show little autocorrelation. Squared returns
                  often show a lot, because large moves tend to follow large moves. That pattern is what GARCH
                  models describe, and it is the subject of the next phases.
                </p>
              </div>
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
