import { useEffect, useRef } from "react";
import { BaselineSeries, HistogramSeries, createChart } from "lightweight-charts";
import type { Point } from "../../types/api";
import { useTheme } from "../../theme";
import { formatNumber } from "../../utils/format";
import { baseOptions, readColors, withAlpha } from "./chartTheme";

interface Props {
  points: Point[];
  /** "area" fills above and below zero. "bars" draws one bar per day. */
  kind: "area" | "bars";
  label: string;
  height?: number;
}

/** Percent valued series centred on zero: cumulative return or daily returns. */
export default function SeriesChart({ points, kind, label, height = 260 }: Props) {
  const { theme } = useTheme();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || points.length === 0) return;
    const c = readColors();
    const chart = createChart(el, baseOptions(c, height, (p) => `${formatNumber(p, 2)}%`));

    if (kind === "area") {
      const s = chart.addSeries(BaselineSeries, {
        baseValue: { type: "price", price: 0 },
        topLineColor: c.up, topFillColor1: withAlpha(c.up, 0.3), topFillColor2: withAlpha(c.up, 0.02),
        bottomLineColor: c.down, bottomFillColor1: withAlpha(c.down, 0.02), bottomFillColor2: withAlpha(c.down, 0.3),
        lineWidth: 2, priceLineVisible: false,
      });
      s.setData(points.map((p) => ({ time: p.date, value: p.value })));
    } else {
      const s = chart.addSeries(HistogramSeries, { priceLineVisible: false });
      s.setData(points.map((p) => ({ time: p.date, value: p.value, color: p.value >= 0 ? c.up : c.down })));
    }
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [points, kind, height, theme]);

  return <div ref={ref} role="img" aria-label={label} style={{ height }} />;
}
