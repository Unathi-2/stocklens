import { useEffect, useRef } from "react";
import { AreaSeries, LineSeries, createChart } from "lightweight-charts";
import type { Point } from "../../types/api";
import { useTheme } from "../../theme";
import { formatNumber } from "../../utils/format";
import { baseOptions, readColors, withAlpha } from "./chartTheme";

/** Percent below the running peak. Always zero or negative. */
export function DrawdownChart({ points, height = 240 }: { points: Point[]; height?: number }) {
  const { theme } = useTheme();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || points.length === 0) return;
    const c = readColors();
    const chart = createChart(el, baseOptions(c, height, (p) => `${formatNumber(p, 1)}%`));
    const s = chart.addSeries(AreaSeries, {
      lineColor: c.down, topColor: withAlpha(c.down, 0.02), bottomColor: withAlpha(c.down, 0.3),
      lineWidth: 2, priceLineVisible: false, invertFilledArea: true,
      autoscaleInfoProvider: (original: () => { priceRange: { minValue: number; maxValue: number } | null } | null) => {
        const r = original();
        if (r?.priceRange) r.priceRange.maxValue = 1; // drawdown is never positive, so keep the axis tight
        return r;
      },
    });
    s.setData(points.map((p) => ({ time: p.date, value: p.value })));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [points, height, theme]);

  return <div ref={ref} role="img" aria-label="Drawdown from the previous peak, in percent" style={{ height }} />;
}

export interface VolSeries {
  name: string;
  /** "accent", "amber" and "muted" follow the theme. Anything else is used as a colour value. */
  color: string;
  points: Point[];
}

const AMBER = "#d9992b"; // reads on both themes, same family as the moving average colours

/** One or more annualised volatility lines, in percent. */
export function VolatilityChart({ series, label, height = 260 }: { series: VolSeries[]; label: string; height?: number }) {
  const { theme } = useTheme();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || series.every((s) => s.points.length === 0)) return;
    const c = readColors();
    const chart = createChart(el, baseOptions(c, height, (p) => `${formatNumber(p, 1)}%`));
    for (const s of series) {
      const line = chart.addSeries(LineSeries, {
        color: s.color === "accent" ? c.accent : s.color === "amber" ? AMBER : s.color === "muted" ? c.muted : s.color,
        lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      });
      line.setData(s.points.map((p) => ({ time: p.date, value: p.value })));
    }
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [series, height, theme]);

  return <div ref={ref} role="img" aria-label={label} style={{ height }} />;
}

/** Colour key shown under a chart. Colour is never the only cue, each entry is named. */
export function Legend({ series }: { series: Pick<VolSeries, "name" | "color">[] }) {
  const css = (color: string) => (color === "accent" ? "var(--accent)" : color === "amber" ? AMBER : color === "muted" ? "var(--muted)" : color);
  return (
    <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
      {series.map((s) => (
        <li key={s.name} className="flex items-center gap-2">
          <span aria-hidden className="inline-block h-0.5 w-5" style={{ background: css(s.color) }} />
          {s.name}
        </li>
      ))}
    </ul>
  );
}
