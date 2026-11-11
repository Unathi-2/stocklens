import type { ReactNode } from "react";

export function niceTicks(min: number, max: number, target = 5): number[] {
  const span = max - min || 1;
  const raw = span / target;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const norm = raw / mag;
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
  const out: number[] = [];
  for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-9; v += step) out.push(Number(v.toFixed(10)));
  return out;
}

const linear = (d0: number, d1: number, r0: number, r1: number) => (v: number) => r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);

export interface Frame {
  sx: (v: number) => number;
  sy: (v: number) => number;
  left: number;
  right: number;
  top: number;
  bottom: number;
}

interface Props {
  label: string;
  xDomain: [number, number];
  yDomain: [number, number];
  xLabel: string;
  yLabel: string;
  xFormat?: (v: number) => string;
  yFormat?: (v: number) => string;
  height?: number;
  children: (f: Frame) => ReactNode;
}

const W = 640;
const M = { top: 12, right: 16, bottom: 42, left: 56 };
const rule = { stroke: "var(--rule)" } as const;
const muted = { fill: "var(--muted)" } as const;

/** Axes, gridlines and labels for the diagnostic charts. Children draw inside the plot area. */
export function ChartFrame({ label, xDomain, yDomain, xLabel, yLabel, xFormat = String, yFormat = String, height = 300, children }: Props) {
  const frame: Frame = {
    left: M.left,
    right: W - M.right,
    top: M.top,
    bottom: height - M.bottom,
    sx: linear(xDomain[0], xDomain[1], M.left, W - M.right),
    sy: linear(yDomain[0], yDomain[1], height - M.bottom, M.top),
  };
  const xt = niceTicks(...xDomain, 6);
  const yt = niceTicks(...yDomain, 5);

  return (
    <svg viewBox={`0 0 ${W} ${height}`} role="img" aria-label={label} className="h-auto w-full">
      {yt.map((v) => (
        <g key={`y${v}`}>
          <line x1={frame.left} x2={frame.right} y1={frame.sy(v)} y2={frame.sy(v)} style={rule} strokeWidth={1} />
          <text x={frame.left - 8} y={frame.sy(v)} textAnchor="end" dominantBaseline="middle" fontSize={11} style={muted}>
            {yFormat(v)}
          </text>
        </g>
      ))}
      {xt.map((v) => (
        <g key={`x${v}`}>
          <line x1={frame.sx(v)} x2={frame.sx(v)} y1={frame.bottom} y2={frame.bottom + 4} style={rule} />
          <text x={frame.sx(v)} y={frame.bottom + 16} textAnchor="middle" fontSize={11} style={muted}>
            {xFormat(v)}
          </text>
        </g>
      ))}
      <line x1={frame.left} x2={frame.right} y1={frame.bottom} y2={frame.bottom} style={rule} />
      <text x={(frame.left + frame.right) / 2} y={height - 6} textAnchor="middle" fontSize={11} style={muted}>{xLabel}</text>
      <text transform={`translate(12 ${(frame.top + frame.bottom) / 2}) rotate(-90)`} textAnchor="middle" fontSize={11} style={muted}>{yLabel}</text>
      {children(frame)}
    </svg>
  );
}
