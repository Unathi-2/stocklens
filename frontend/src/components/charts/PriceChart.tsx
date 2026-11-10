import { useEffect, useMemo, useRef, useState } from "react";
import { AreaSeries, CandlestickSeries, HistogramSeries, LineSeries, createChart } from "lightweight-charts";
import type { Bar, IndicatorSeries } from "../../types/api";
import { useTheme } from "../../theme";
import { formatCompact, formatDate, formatPrice } from "../../utils/format";
import { INDICATOR_COLORS, baseOptions, readColors, withAlpha } from "./chartTheme";
import PriceChange from "../ui/PriceChange";

interface Props {
  bars: Bar[];
  indicators: IndicatorSeries[];
  /** Which moving averages to draw, keyed like "sma20". */
  visible: Record<string, boolean>;
  kind: "line" | "candles";
  showVolume: boolean;
  currency: string;
  assetType: string;
  height?: number;
}

export const indicatorKey = (i: IndicatorSeries) => `${i.kind}${i.window}`;

export default function PriceChart({ bars, indicators, visible, kind, showVolume, currency, assetType, height = 420 }: Props) {
  const { theme } = useTheme();
  const ref = useRef<HTMLDivElement>(null);
  const [hoverDate, setHoverDate] = useState<string | null>(null);

  const hasVolume = bars.some((b) => b.volume > 0);
  const volumeOn = showVolume && hasVolume;

  const index = useMemo(() => new Map(bars.map((b, i) => [b.date, i])), [bars]);

  useEffect(() => {
    const el = ref.current;
    if (!el || bars.length === 0) return;
    const c = readColors();
    const chart = createChart(el, baseOptions(c, height, (p) => formatPrice(p, currency, assetType)));
    chart.priceScale("right").applyOptions({ scaleMargins: { top: 0.08, bottom: volumeOn ? 0.28 : 0.08 } });

    if (kind === "candles") {
      const s = chart.addSeries(CandlestickSeries, {
        upColor: c.up, downColor: c.down, borderVisible: false,
        wickUpColor: c.up, wickDownColor: c.down, priceLineVisible: false,
      });
      s.setData(bars.map((b) => ({ time: b.date, open: b.open, high: b.high, low: b.low, close: b.close })));
    } else {
      const s = chart.addSeries(AreaSeries, {
        lineColor: c.accent, lineWidth: 2,
        topColor: withAlpha(c.accent, 0.22), bottomColor: withAlpha(c.accent, 0),
        priceLineVisible: false,
      });
      s.setData(bars.map((b) => ({ time: b.date, value: b.close })));
    }

    for (const ind of indicators) {
      const key = indicatorKey(ind);
      if (!visible[key]) continue;
      const line = chart.addSeries(LineSeries, {
        color: INDICATOR_COLORS[key] ?? c.muted, lineWidth: 1,
        priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      });
      line.setData(ind.points.map((p) => ({ time: p.date, value: p.value })));
    }

    if (volumeOn) {
      const vol = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" }, priceScaleId: "", lastValueVisible: false, priceLineVisible: false,
      });
      chart.priceScale("").applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
      vol.setData(
        bars.map((b) => ({ time: b.date, value: b.volume, color: withAlpha(b.close >= b.open ? c.up : c.down, 0.45) })),
      );
    }

    chart.timeScale().fitContent();
    chart.subscribeCrosshairMove((p) => setHoverDate(p.time ? String(p.time) : null));
    return () => chart.remove();
  }, [bars, indicators, visible, kind, volumeOn, currency, assetType, height, theme]);

  const shownIdx = hoverDate && index.has(hoverDate) ? index.get(hoverDate)! : bars.length - 1;
  const bar = bars[shownIdx];
  const prev = shownIdx > 0 ? bars[shownIdx - 1] : null;
  const money = (v: number) => formatPrice(v, currency, assetType);

  return (
    <div>
      <div className="num flex min-h-[2.5rem] flex-wrap items-center gap-x-5 gap-y-1 px-4 py-2 text-sm" aria-live="off">
        {bar ? (
          <>
            <span className="font-medium">{formatDate(bar.date)}</span>
            <span><span className="text-muted">Open </span>{money(bar.open)}</span>
            <span><span className="text-muted">High </span>{money(bar.high)}</span>
            <span><span className="text-muted">Low </span>{money(bar.low)}</span>
            <span><span className="text-muted">Close </span>{money(bar.close)}</span>
            {prev && <PriceChange value={(bar.close / prev.close - 1) * 100} />}
            {hasVolume && <span><span className="text-muted">Volume </span>{formatCompact(bar.volume)}</span>}
          </>
        ) : (
          <span className="text-muted">No price data in this range.</span>
        )}
      </div>
      <div
        ref={ref}
        role="img"
        aria-label={bar ? `Price chart, ${bars.length} points, latest close ${money(bars[bars.length - 1].close)}` : "Price chart"}
        style={{ height }}
      />
    </div>
  );
}
