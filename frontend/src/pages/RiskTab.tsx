import { useMemo, useState, type ReactNode } from "react";
import { Legend, DrawdownChart, VolatilityChart, type VolSeries } from "../components/charts/RiskCharts";
import { formatP } from "../components/stats/TestResultCard";
import Badge from "../components/ui/Badge";
import DataTable, { type Column } from "../components/ui/DataTable";
import { ErrorMessage, LoadingSpinner, Skeleton } from "../components/ui/Feedback";
import { Ledger, MetricCard } from "../components/ui/Ledger";
import Panel from "../components/ui/Panel";
import { useApi } from "../hooks/useApi";
import { useDebounce } from "../hooks/useDebounce";
import { api } from "../services/api";
import type { Backtest, Period, VarRow } from "../types/api";
import { formatDate, formatNumber } from "../utils/format";

interface Props {
  symbol: string;
  exchange?: string;
  period: Period;
  periodControl: ReactNode;
}

const pct = (v: number | null | undefined, d = 2) => (v == null ? "n/a" : `${formatNumber(v, d)}%`);
const conf = (c: number) => `${Math.round(c * 100)}%`;

const VAR_COLUMNS: Column<VarRow>[] = [
  { key: "c", header: "Confidence", render: (r) => conf(r.confidence) },
  { key: "hv", header: "Historical VaR", align: "right", render: (r) => pct(r.historical_var_pct) },
  { key: "nv", header: "Normal VaR", align: "right", render: (r) => pct(r.normal_var_pct) },
  { key: "cf", header: "Cornish-Fisher VaR", align: "right", render: (r) => pct(r.cornish_fisher_var_pct) },
  { key: "he", header: "Historical ES", align: "right", render: (r) => pct(r.historical_es_pct) },
  { key: "ne", header: "Normal ES", align: "right", render: (r) => pct(r.normal_es_pct) },
];

function BacktestCard({ b }: { b: Backtest }) {
  return (
    <article className="flex flex-col gap-2 rounded-md border border-rule bg-panel p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-serif text-lg leading-tight">Kupiec test, {conf(b.confidence)} VaR</h3>
        <Badge tone={b.reject_null ? "down" : "neutral"}>
          {b.reject_null ? "Evidence against" : "Insufficient evidence to reject"}
        </Badge>
      </header>
      <p className="text-sm text-muted">H0: the share of days with a loss beyond VaR equals {formatNumber(100 - b.confidence * 100, 0)}%.</p>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <dt className="text-muted">Days tested</dt><dd className="num text-right">{formatNumber(b.tests, 0)}</dd>
        <dt className="text-muted">Violations</dt><dd className="num text-right">{b.violations}</dd>
        <dt className="text-muted">Expected</dt><dd className="num text-right">{formatNumber(b.expected_violations, 1)}</dd>
        <dt className="text-muted">Violation rate</dt><dd className="num text-right">{pct(b.violation_rate_pct)}</dd>
        <dt className="text-muted">LR statistic</dt><dd className="num text-right">{formatNumber(b.lr_statistic, 3)}</dd>
        <dt className="text-muted">p value</dt><dd className="num text-right">{formatP(b.p_value)}</dd>
      </dl>
    </article>
  );
}

/** Mounted only while the tab is open, so the heavier request runs on demand. */
export default function RiskTab({ symbol, exchange, period, periodControl }: Props) {
  const [rfText, setRfText] = useState("0");
  const rfParsed = Number(rfText);
  const rfValid = rfText.trim() !== "" && Number.isFinite(rfParsed) && rfParsed >= 0 && rfParsed <= 30;
  const rf = useDebounce(rfValid ? rfParsed : 0, 500);

  const risk = useApi(() => api.getRisk(symbol, { period, risk_free: rf, exchange }), [symbol, exchange, period, rf]);
  const d = risk.data;

  const rolling: VolSeries[] = useMemo(
    () => (d?.rolling_volatility ?? []).map((r) => ({
      name: `${r.window} day realised`, color: r.window === 21 ? "accent" : "amber", points: r.points,
    })),
    [d],
  );
  const garchSeries: VolSeries[] = useMemo(() => {
    if (!d?.garch) return [];
    const r21 = rolling.find((s) => s.name.startsWith("21"));
    return [
      { name: "GARCH(1,1) conditional", color: "accent", points: d.garch.volatility },
      ...(r21 ? [{ name: "21 day realised", color: "muted" as const, points: r21.points }] : []),
    ];
  }, [d, rolling]);

  const s = d?.summary;
  const dd = d?.drawdown;
  const g = d?.garch;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        {periodControl}
        <div className="flex items-center gap-3">
          {risk.loading && d && <LoadingSpinner label="Updating" />}
          <label className="flex items-center gap-2 text-sm text-muted">
            Risk free rate, % a year
            <input
              type="number" inputMode="decimal" min={0} max={30} step={0.25}
              value={rfText} onChange={(e) => setRfText(e.target.value)}
              aria-invalid={!rfValid}
              className="num w-20 rounded border border-rule bg-panel px-2 py-1 text-ink"
            />
          </label>
        </div>
      </div>
      {!rfValid && <p role="alert" className="text-sm text-down">Enter a rate between 0 and 30.</p>}

      {risk.error ? (
        <ErrorMessage message={risk.error.message} onRetry={risk.reload} />
      ) : !d || !s || !dd ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-[260px] w-full" />
        </div>
      ) : (
        <>
          <Ledger className="grid-cols-2 lg:grid-cols-3">
            <MetricCard label="Annualised return" value={pct(s.annualised_return_pct)} note={<span className="text-muted">Compound rate</span>} />
            <MetricCard label="Annualised volatility" value={pct(s.annualised_volatility_pct)} />
            <MetricCard label="Maximum drawdown" value={pct(dd.max_drawdown_pct)} />
            <MetricCard label="Sharpe ratio" value={formatNumber(s.sharpe, 2)} note={<span className="text-muted">Return per unit of volatility</span>} />
            <MetricCard label="Sortino ratio" value={formatNumber(s.sortino, 2)} note={<span className="text-muted">Counts only downside</span>} />
            <MetricCard label="Calmar ratio" value={formatNumber(s.calmar, 2)} note={<span className="text-muted">Return per unit of drawdown</span>} />
          </Ledger>

          <Panel title="Drawdown">
            <DrawdownChart points={dd.series} />
            <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm lg:grid-cols-5">
              <div><dt className="text-muted">Worst peak</dt><dd className="num">{formatDate(dd.peak_date)}</dd></div>
              <div><dt className="text-muted">Worst trough</dt><dd className="num">{formatDate(dd.trough_date)}</dd></div>
              <div><dt className="text-muted">Recovered</dt><dd className="num">{dd.trough_date ? (dd.recovery_date ? formatDate(dd.recovery_date) : "Not yet") : "n/a"}</dd></div>
              <div><dt className="text-muted">Now</dt><dd className="num">{pct(dd.current_drawdown_pct)} from the peak</dd></div>
              <div><dt className="text-muted">Longest time below a peak</dt><dd className="num">{formatNumber(dd.longest_underwater_days, 0)} trading days</dd></div>
            </dl>
          </Panel>

          <Panel title="Rolling volatility">
            <VolatilityChart series={rolling} label="Rolling annualised volatility in percent" />
            <Legend series={rolling} />
            <p className="mt-3 max-w-prose text-sm text-muted">
              Annualised standard deviation of daily log returns over the last 21 and 63 trading days. The shorter
              window reacts faster and is noisier.
            </p>
          </Panel>

          <section aria-labelledby="var-heading" className="space-y-3">
            <h2 id="var-heading" className="font-serif text-xl">Value at risk and expected shortfall</h2>
            <Panel flush>
              <DataTable columns={VAR_COLUMNS} rows={d.var} rowKey={(r) => String(r.confidence)} />
            </Panel>
            <p className="max-w-prose text-sm text-muted">
              One day horizon, as a percent of the position. At 95% confidence the historical VaR is the loss that
              was exceeded on 1 day in 20 in this window. Expected shortfall is the average loss on those days.
              When the normal figures sit well below the historical ones, the returns have fatter tails than a
              normal distribution, and the Cornish-Fisher figure adjusts for that using skewness and kurtosis.
            </p>
            {d.backtests.length > 0 ? (
              <div className="grid gap-4 lg:grid-cols-2">
                {d.backtests.map((b) => <BacktestCard key={b.confidence} b={b} />)}
              </div>
            ) : (
              <p className="max-w-prose text-sm text-muted">
                The VaR backtest needs more than 350 daily returns. Choose 5Y or Max to see it.
              </p>
            )}
            {d.backtests.length > 0 && (
              <p className="max-w-prose text-sm text-muted">
                Each day's VaR is computed from the previous 250 returns only, then compared with the next day's
                return. A p value below 0.05 is evidence that the violation rate differs from the target.
              </p>
            )}
          </section>

          <Panel title="GARCH(1,1) conditional volatility">
            {!g ? (
              <p className="max-w-prose text-sm text-muted">
                A GARCH fit needs at least 500 daily returns, about two years. Choose 5Y or Max.
              </p>
            ) : (
              <div className="space-y-4">
                {!g.converged && <Badge tone="down">The optimiser did not report convergence, treat the estimates with caution</Badge>}
                <Ledger className="grid-cols-2 lg:grid-cols-4">
                  <MetricCard label="Persistence" value={formatNumber(g.persistence, 3)} note={<span className="text-muted">alpha plus beta</span>} />
                  <MetricCard label="Half life of a shock" value={g.half_life_days == null ? "n/a" : `${formatNumber(g.half_life_days, 1)} days`} />
                  <MetricCard label="Long run volatility" value={pct(g.unconditional_volatility_pct)} />
                  <MetricCard label="Latest volatility" value={pct(g.latest_volatility_pct)} />
                </Ledger>
                <VolatilityChart series={garchSeries} label="GARCH conditional volatility against 21 day realised volatility" />
                <Legend series={garchSeries} />
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse text-sm">
                    <thead>
                      <tr className="text-left text-muted">
                        <th className="py-1 pr-4 font-medium">Parameter</th>
                        <th className="py-1 pr-4 text-right font-medium">Estimate</th>
                        <th className="py-1 pr-4 text-right font-medium">Std error</th>
                        <th className="py-1 text-right font-medium">p value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {g.parameters.map((p) => (
                        <tr key={p.name} className="border-t border-rule">
                          <td className="py-1.5 pr-4">{p.name}</td>
                          <td className="num py-1.5 pr-4 text-right">{formatNumber(p.estimate, 4)}</td>
                          <td className="num py-1.5 pr-4 text-right">{p.std_error == null ? "n/a" : formatNumber(p.std_error, 4)}</td>
                          <td className="num py-1.5 text-right">{p.p_value == null ? "n/a" : formatP(p.p_value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="max-w-prose text-sm text-muted">
                  Model: daily returns in percent with a constant mean and normal errors, variance equal to omega plus
                  alpha times the last squared shock plus beta times the last variance. Values near 1 for persistence
                  mean volatility shocks fade slowly. Log likelihood {formatNumber(g.log_likelihood, 1)}, AIC{" "}
                  {formatNumber(g.aic, 1)}, BIC {formatNumber(g.bic, 1)}. Other GARCH family models, fat tailed errors
                  and forecasts come in the next phase.
                </p>
              </div>
            )}
          </Panel>

          <p className="max-w-prose text-sm text-muted">
            Sharpe and Sortino subtract a risk free rate of {formatNumber(s.risk_free_pct, 2)}% a year. All measures
            describe the past window shown and do not predict future losses.
          </p>
        </>
      )}
    </div>
  );
}
