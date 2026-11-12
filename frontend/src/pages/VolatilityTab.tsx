import { useMemo, useState, type ReactNode } from "react";
import { NewsImpactChart } from "../components/charts/ModelCharts";
import { Legend, VolatilityChart, type VolSeries } from "../components/charts/RiskCharts";
import { formatP } from "../components/stats/TestResultCard";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import DataTable, { type Column } from "../components/ui/DataTable";
import { ErrorMessage, LoadingSpinner } from "../components/ui/Feedback";
import Panel from "../components/ui/Panel";
import RangeSelector from "../components/ui/RangeSelector";
import Toggle from "../components/ui/Toggle";
import { useApi } from "../hooks/useApi";
import { api } from "../services/api";
import type { Period, VolatilityModels, VolModel } from "../types/api";
import { formatDate, formatNumber } from "../utils/format";
import { MODEL_COLORS } from "../utils/models";

interface Props {
  symbol: string;
  exchange?: string;
  period: Period;
  periodControl: ReactNode;
}

const DESCRIPTIONS: Record<string, string> = {
  sgarch: "Variance depends on the last squared shock and the last variance. Gains and losses of the same size count equally.",
  egarch: "Models the logarithm of variance, so it needs no sign limits on parameters. A gamma below 0 means falls raise volatility more than rises.",
  gjr: "Adds an extra term when the shock is negative, so bad news can raise volatility more than good news.",
  figarch: "Fractionally integrated: shocks fade at a slow hyperbolic rate instead of a geometric one. A d near 0 is short memory, near 1 is very long memory.",
  fgarch: "Hentschel's family model with a power delta, an asymmetry eta1 and a shift eta2 of the news impact curve. It contains GARCH, GJR and APARCH as special cases.",
  aparch: "Asymmetric power ARCH: a power delta on volatility and an asymmetry gamma. With delta 2 and gamma 0 it is sGARCH.",
};

const LONG_PERIODS: Period[] = ["5y", "max"];
const pct = (v: number | null | undefined, d = 2) => (v == null ? "n/a" : `${formatNumber(v, d)}%`);

const toPoints = (dates: string[], values: (number | null)[]) =>
  dates.flatMap((date, i) => (values[i] == null ? [] : [{ date, value: values[i] as number }]));

function ResidualLine({ label, p }: { label: string; p: number }) {
  const reject = p < 0.05;
  return (
    <li className="flex flex-wrap items-center justify-between gap-2">
      <span className="text-muted">{label}</span>
      <span className="flex items-center gap-2">
        <span className="num">p {formatP(p)}</span>
        <Badge tone={reject ? "down" : "neutral"}>{reject ? "Evidence against" : "Insufficient evidence to reject"}</Badge>
      </span>
    </li>
  );
}

function ModelDetails({ m }: { m: VolModel }) {
  return (
    <details className="group border-t border-rule first:border-t-0">
      <summary className="flex cursor-pointer flex-wrap items-center justify-between gap-2 px-4 py-3 text-sm marker:content-none">
        <span className="flex items-center gap-2">
          <span aria-hidden className="inline-block h-2 w-2 rounded-full" style={{ background: MODEL_COLORS[m.id] }} />
          <span className="font-medium">{m.name}</span>
        </span>
        {m.error ? <Badge tone="down">Fit failed</Badge> : !m.converged ? <Badge tone="down">No convergence reported</Badge> : null}
      </summary>
      <div className="space-y-3 px-4 pb-4">
        <p className="max-w-prose text-sm text-muted">{DESCRIPTIONS[m.id]}</p>
        {m.error ? (
          <p className="text-sm text-down">{m.error}</p>
        ) : (
          <>
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
                  {m.parameters.map((p) => (
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
            {m.parameters.some((p) => p.std_error == null) && (
              <p className="max-w-prose text-sm text-muted">
                Some standard errors are unavailable. The likelihood is flat in some directions or a parameter sits
                on its limit, so a reliable covariance matrix could not be computed.
              </p>
            )}
            {m.residual_tests && (
              <div>
                <h4 className="mb-1 text-sm font-medium">Checks on standardised residuals</h4>
                <ul className="space-y-1.5 text-sm">
                  <ResidualLine label="Ljung Box, 10 lags, residuals" p={m.residual_tests.ljung_box_p} />
                  <ResidualLine label="Ljung Box, 10 lags, squared residuals" p={m.residual_tests.ljung_box_squared_p} />
                  <ResidualLine label="Jarque Bera, normality" p={m.residual_tests.jarque_bera_p} />
                </ul>
              </div>
            )}
          </>
        )}
      </div>
    </details>
  );
}

function Results({ symbol, exchange, period }: { symbol: string; exchange?: string; period: Period }) {
  const res = useApi(() => api.getVolatilityModels(symbol, { period, exchange }), [symbol, exchange, period]);
  const d = res.data;
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [range, setRange] = useState<"1y" | "all">("1y");
  const isOn = (id: string) => visible[id] ?? true;

  const fitted = useMemo(() => (d ? d.models.filter((m) => m.converged && m.volatility.length > 0) : []), [d]);

  const path: VolSeries[] = useMemo(() => {
    if (!d) return [];
    const from = range === "1y" ? Math.max(0, d.dates.length - 252) : 0;
    const dates = d.dates.slice(from);
    return [
      ...fitted.filter((m) => isOn(m.id)).map((m) => ({ name: m.name, color: MODEL_COLORS[m.id], points: toPoints(dates, m.volatility.slice(from)) })),
      { name: "21 day realised", color: "muted", points: toPoints(dates, d.realised_21d.slice(from)) },
    ];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d, fitted, visible, range]);

  const forecast: VolSeries[] = useMemo(
    () => (d ? fitted.filter((m) => isOn(m.id)).map((m) => ({ name: m.name, color: MODEL_COLORS[m.id], points: toPoints(d.forecast_dates, m.forecast) })) : []),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [d, fitted, visible],
  );

  const nic = useMemo(
    () => fitted.filter((m) => isOn(m.id) && m.news_impact).map((m) => ({ name: m.name, color: MODEL_COLORS[m.id], x: m.news_impact!.shock, y: m.news_impact!.volatility })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [fitted, visible],
  );

  if (res.error) return <ErrorMessage message={res.error.message} onRetry={res.reload} />;
  if (!d) return <LoadingSpinner label="Fitting six models. This can take several seconds." />;

  const bestAic = d.models.find((m) => m.id === d.best_aic)?.aic ?? null;
  const columns: Column<VolModel>[] = [
    {
      key: "name", header: "Model", sortValue: (m) => m.name,
      render: (m) => (
        <span className="flex flex-wrap items-center gap-2">
          <span aria-hidden className="inline-block h-2 w-2 rounded-full" style={{ background: MODEL_COLORS[m.id] }} />
          {m.name}
          {m.id === d.best_aic && <Badge tone="up">Lowest AIC</Badge>}
          {m.id === d.best_bic && <Badge tone="accent">Lowest BIC</Badge>}
          {!m.converged && <Badge tone="down">{m.error ? "Failed" : "No convergence"}</Badge>}
        </span>
      ),
    },
    { key: "ll", header: "Log likelihood", align: "right", sortValue: (m) => m.log_likelihood ?? -Infinity, render: (m) => formatNumber(m.log_likelihood, 1) },
    { key: "k", header: "Parameters", align: "right", sortValue: (m) => m.n_params ?? 0, render: (m) => (m.n_params ?? "n/a") },
    { key: "aic", header: "AIC", align: "right", sortValue: (m) => m.aic ?? Infinity, render: (m) => formatNumber(m.aic, 1) },
    {
      key: "daic", header: "AIC gap", align: "right", sortValue: (m) => (m.aic == null || bestAic == null ? Infinity : m.aic - bestAic),
      render: (m) => (m.aic == null || bestAic == null ? "n/a" : formatNumber(m.aic - bestAic, 1)),
    },
    { key: "bic", header: "BIC", align: "right", sortValue: (m) => m.bic ?? Infinity, render: (m) => formatNumber(m.bic, 1) },
    {
      key: "pers", header: "Persistence", align: "right", sortValue: (m) => m.persistence ?? -Infinity,
      render: (m) => (m.persistence != null ? formatNumber(m.persistence, 3) : m.memory_d != null ? `d = ${formatNumber(m.memory_d, 2)}` : "n/a"),
    },
    { key: "hl", header: "Half life", align: "right", sortValue: (m) => m.half_life_days ?? Infinity, render: (m) => (m.half_life_days == null ? "n/a" : `${formatNumber(m.half_life_days, 1)} days`) },
    { key: "f1", header: "Forecast, 1 day", align: "right", sortValue: (m) => m.forecast[0] ?? 0, render: (m) => pct(m.forecast[0], 1) },
    { key: "f10", header: `Forecast, ${d.horizon} days`, align: "right", sortValue: (m) => m.forecast[d.horizon - 1] ?? 0, render: (m) => pct(m.forecast[d.horizon - 1], 1) },
    { key: "lb2", header: "Squared residuals, Ljung Box p", align: "right", sortValue: (m) => m.residual_tests?.ljung_box_squared_p ?? -1, render: (m) => (m.residual_tests ? formatP(m.residual_tests.ljung_box_squared_p) : "n/a") },
  ];

  return (
    <div className="space-y-6">
      <Panel title="Model comparison" flush>
        <DataTable columns={columns} rows={d.models} rowKey={(m) => m.id} />
      </Panel>
      <p className="max-w-prose text-sm text-muted">
        {d.observations} daily returns, normal errors and a constant mean for every model. Lower AIC and BIC are
        better, and BIC penalises extra parameters more. The AIC gap is the distance from the best model, and a gap
        under about 2 means the data cannot separate the two. Persistence is how fast the variance process forgets a
        shock, half life is the days for a shock to lose half its effect, and FIGARCH reports its memory parameter d
        instead. Forecasts are annualised volatility. A small p value in the last column is evidence that
        volatility clustering is left in the residuals.
      </p>

      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Models shown in the charts">
        <span className="text-sm text-muted">Show in charts</span>
        {fitted.map((m) => (
          <Toggle key={m.id} pressed={isOn(m.id)} onChange={(on) => setVisible((v) => ({ ...v, [m.id]: on }))} swatch={MODEL_COLORS[m.id]}>
            {m.name}
          </Toggle>
        ))}
      </div>

      <Panel
        title="Fitted conditional volatility"
        action={
          <RangeSelector
            label="Chart range" value={range} onChange={setRange}
            options={[{ value: "1y", label: "Last year" }, { value: "all", label: "Whole window" }]}
          />
        }
      >
        <VolatilityChart series={path} label="Conditional volatility from each model against 21 day realised volatility" height={300} />
        <Legend series={path} />
        <p className="mt-3 max-w-prose text-sm text-muted">
          The models track the same swings and differ mostly after large moves. Annualised, in percent.
        </p>
      </Panel>

      <Panel title={`Volatility forecast, next ${d.horizon} trading days`}>
        <VolatilityChart series={forecast} label="Forecast annualised volatility from each model" height={260} />
        <Legend series={forecast} />
        <p className="mt-3 max-w-prose text-sm text-muted">
          From {formatDate(d.forecast_dates[0])} to {formatDate(d.forecast_dates[d.forecast_dates.length - 1])}. Forecasts
          drift toward each model's long run level. sGARCH, GJR and FIGARCH use exact formulas. EGARCH, APARCH and
          fGARCH use 5,000 simulated paths with a fixed seed. These are model outputs, not predictions of prices.
        </p>
      </Panel>

      <Panel title="News impact curves">
        <NewsImpactChart series={nic} />
        <Legend series={nic} />
        <p className="mt-3 max-w-prose text-sm text-muted">
          How much tomorrow's volatility rises after a shock of a given size and sign, starting from each model's
          average volatility. A symmetric curve (sGARCH) treats gains and losses alike. A higher left side means
          losses raise volatility more, the leverage effect. FIGARCH has no one step curve and is not drawn.
        </p>
      </Panel>

      <Panel title="Parameters and residual checks" flush>
        {d.models.map((m) => <ModelDetails key={m.id} m={m} />)}
      </Panel>
    </div>
  );
}

export default function VolatilityTab({ symbol, exchange, period, periodControl }: Props) {
  const [run, setRun] = useState(false);
  const longEnough = LONG_PERIODS.includes(period);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">{periodControl}</div>

      <Panel title="Six volatility models">
        <ul className="grid gap-x-8 gap-y-2 text-sm lg:grid-cols-2">
          {Object.entries(DESCRIPTIONS).map(([id, text]) => (
            <li key={id} className="flex gap-2">
              <span aria-hidden className="mt-1.5 inline-block h-2 w-2 shrink-0 rounded-full" style={{ background: MODEL_COLORS[id] }} />
              <span><span className="font-medium">{{ sgarch: "sGARCH", egarch: "EGARCH", gjr: "GJR-GARCH", figarch: "FIGARCH", fgarch: "fGARCH", aparch: "APARCH" }[id]}.</span>{" "}<span className="text-muted">{text}</span></span>
            </li>
          ))}
        </ul>
      </Panel>

      {!longEnough ? (
        <p className="max-w-prose text-sm text-muted">
          These models need at least 500 daily returns, about two years. Choose 5Y or Max to fit them.
        </p>
      ) : !run ? (
        <div className="flex flex-wrap items-center gap-4">
          <Button onClick={() => setRun(true)}>Fit the six models</Button>
          <span className="text-sm text-muted">Fitting takes a few seconds the first time. Results are kept for repeat visits.</span>
        </div>
      ) : (
        <Results symbol={symbol} exchange={exchange} period={period} />
      )}
    </div>
  );
}
