import { ChartFrame } from "./svg";

export interface CurveSeries {
  name: string;
  color: string;
  x: number[];
  y: number[];
}

/** Next day volatility against the size of today's shock, one line per model. */
export function NewsImpactChart({ series }: { series: CurveSeries[] }) {
  const ys = series.flatMap((s) => s.y);
  const lo = Math.min(...ys);
  const hi = Math.max(...ys);
  const pad = (hi - lo) * 0.08 || 1;
  return (
    <ChartFrame
      label="News impact curves: next day volatility after a shock of a given size"
      xDomain={[-4, 4]}
      yDomain={[Math.max(0, lo - pad), hi + pad]}
      xLabel="Today's return shock, in standard deviations"
      yLabel="Next day volatility (% a year)"
      yFormat={(v) => v.toFixed(0)}
      height={320}
    >
      {(f) => (
        <>
          <line x1={f.sx(0)} x2={f.sx(0)} y1={f.top} y2={f.bottom} style={{ stroke: "var(--rule)" }} strokeDasharray="4 4" />
          {series.map((s) => (
            <polyline
              key={s.name}
              fill="none"
              strokeWidth={2}
              style={{ stroke: s.color }}
              points={s.x.map((x, i) => `${f.sx(x)},${f.sy(s.y[i])}`).join(" ")}
            />
          ))}
        </>
      )}
    </ChartFrame>
  );
}
