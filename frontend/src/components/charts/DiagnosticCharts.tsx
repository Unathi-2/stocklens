import { ChartFrame } from "./svg";

const accent = "var(--accent)";
const ink = "var(--ink)";
const muted = "var(--muted)";

interface HistogramProps {
  centers: number[];
  density: number[];
  normal: number[];
  binWidth: number;
}

/** Observed return density with the fitted normal curve on top. */
export function Histogram({ centers, density, normal, binWidth }: HistogramProps) {
  const x0 = centers[0] - binWidth / 2;
  const x1 = centers[centers.length - 1] + binWidth / 2;
  const top = Math.max(...density, ...normal) * 1.1;
  return (
    <ChartFrame
      label="Histogram of daily log returns with a fitted normal curve"
      xDomain={[x0, x1]}
      yDomain={[0, top]}
      xLabel="Daily log return (%)"
      yLabel="Density"
      yFormat={(v) => v.toFixed(2)}
    >
      {(f) => (
        <>
          {centers.map((c, i) => (
            <rect
              key={c}
              x={f.sx(c - binWidth / 2) + 0.5}
              y={f.sy(density[i])}
              width={Math.max(f.sx(c + binWidth / 2) - f.sx(c - binWidth / 2) - 1, 1)}
              height={f.sy(0) - f.sy(density[i])}
              style={{ fill: accent, fillOpacity: 0.55 }}
            />
          ))}
          <polyline
            points={centers.map((c, i) => `${f.sx(c)},${f.sy(normal[i])}`).join(" ")}
            fill="none"
            strokeWidth={2}
            strokeDasharray="5 3"
            style={{ stroke: ink }}
          />
          <g fontSize={11} style={{ fill: ink }}>
            <rect x={f.right - 128} y={f.top + 6} width={10} height={10} style={{ fill: accent, fillOpacity: 0.55 }} />
            <text x={f.right - 112} y={f.top + 15}>Observed</text>
            <line x1={f.right - 128} x2={f.right - 118} y1={f.top + 28} y2={f.top + 28} strokeWidth={2} strokeDasharray="4 2" style={{ stroke: ink }} />
            <text x={f.right - 112} y={f.top + 32}>Normal fit</text>
          </g>
        </>
      )}
    </ChartFrame>
  );
}

/** Quantile quantile plot against the normal. Points off the line mean non normal tails. */
export function QQPlot({ theoretical, sample }: { theoretical: number[]; sample: number[] }) {
  const lim = Math.ceil(Math.max(...theoretical.map(Math.abs), ...sample.map(Math.abs)));
  return (
    <ChartFrame
      label="Normal quantile quantile plot of standardised daily log returns"
      xDomain={[-lim, lim]}
      yDomain={[-lim, lim]}
      xLabel="Normal quantiles"
      yLabel="Sample quantiles (standardised)"
    >
      {(f) => (
        <>
          <line x1={f.sx(-lim)} y1={f.sy(-lim)} x2={f.sx(lim)} y2={f.sy(lim)} strokeWidth={1.5} strokeDasharray="5 3" style={{ stroke: muted }} />
          {theoretical.map((t, i) => (
            <circle key={i} cx={f.sx(t)} cy={f.sy(sample[i])} r={1.8} style={{ fill: accent, fillOpacity: 0.65 }} />
          ))}
        </>
      )}
    </ChartFrame>
  );
}

interface CorrProps {
  lags: number[];
  values: number[];
  bound: number;
  label: string;
}

/** Bars outside the dashed 95% band are distinguishable from zero. */
export function CorrelogramChart({ lags, values, bound, label }: CorrProps) {
  const peak = Math.max(bound, ...values.map(Math.abs));
  const y = Math.ceil((peak * 1.15) / 0.05) * 0.05;
  const last = lags[lags.length - 1];
  return (
    <ChartFrame
      label={label}
      xDomain={[0, last + 1]}
      yDomain={[-y, y]}
      xLabel="Lag (trading days)"
      yLabel="Correlation"
      yFormat={(v) => v.toFixed(2)}
      height={240}
    >
      {(f) => (
        <>
          {[bound, -bound].map((b) => (
            <line key={b} x1={f.left} x2={f.right} y1={f.sy(b)} y2={f.sy(b)} strokeWidth={1.2} strokeDasharray="5 3" style={{ stroke: muted }} />
          ))}
          <line x1={f.left} x2={f.right} y1={f.sy(0)} y2={f.sy(0)} style={{ stroke: ink }} strokeWidth={1} />
          {lags.map((lag, i) => (
            <line
              key={lag}
              x1={f.sx(lag)}
              x2={f.sx(lag)}
              y1={f.sy(0)}
              y2={f.sy(values[i])}
              strokeWidth={4}
              style={{ stroke: accent, strokeOpacity: Math.abs(values[i]) > bound ? 1 : 0.4 }}
            />
          ))}
        </>
      )}
    </ChartFrame>
  );
}
