import Badge from "../ui/Badge";
import type { TestResult } from "../../types/api";
import { formatNumber } from "../../utils/format";

const LABELS: Record<string, string> = {
  lags_used: "Lags used",
  observations: "Observations",
  lags: "Lags tested",
  critical_value_1pct: "Critical value 1%",
  critical_value_5pct: "Critical value 5%",
  critical_value_10pct: "Critical value 10%",
  f_statistic: "F statistic",
  f_p_value: "F test p value",
  skewness: "Skewness",
  excess_kurtosis: "Excess kurtosis",
};

export const formatP = (p: number) => (p < 0.0001 ? "< 0.0001" : p.toFixed(4));

export default function TestResultCard({ test }: { test: TestResult }) {
  return (
    <article className="flex flex-col gap-3 rounded-md border border-rule bg-panel p-4">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-serif text-lg leading-tight">{test.name}</h3>
          <p className="text-sm text-muted">{test.applied_to}</p>
        </div>
        <Badge tone={test.reject_null ? "accent" : "neutral"}>
          {test.reject_null ? "Evidence against H0" : "No evidence against H0"}
        </Badge>
      </header>

      <dl className="num grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <dt className="text-muted">Test statistic</dt>
        <dd className="text-right font-medium">{formatNumber(test.statistic, 3)}</dd>
        <dt className="text-muted">p value</dt>
        <dd className="text-right font-medium">{formatP(test.p_value)}</dd>
        {Object.entries(test.details).map(([key, value]) => (
          <div key={key} className="contents">
            <dt className="text-muted">{LABELS[key] ?? key.replace(/_/g, " ")}</dt>
            <dd className="text-right">
              {key.endsWith("p_value") ? formatP(value) : Number.isInteger(value) ? value : formatNumber(value, 3)}
            </dd>
          </div>
        ))}
      </dl>

      <div className="space-y-2 border-t border-rule pt-3 text-sm">
        <p><span className="text-muted">Null hypothesis (H0): </span>{test.null_hypothesis}</p>
        <p>{test.interpretation}</p>
      </div>
    </article>
  );
}
