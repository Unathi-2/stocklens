import { ColorType, CrosshairMode, type ChartOptions, type DeepPartial } from "lightweight-charts";

export interface ChartColors {
  panel: string;
  rule: string;
  ink: string;
  muted: string;
  accent: string;
  up: string;
  down: string;
}

/** Reads the active theme's tokens so charts match the rest of the app. */
export function readColors(): ChartColors {
  const cs = getComputedStyle(document.documentElement);
  const get = (name: string) => cs.getPropertyValue(name).trim();
  return {
    panel: get("--panel"),
    rule: get("--rule"),
    ink: get("--ink"),
    muted: get("--muted"),
    accent: get("--accent"),
    up: get("--up"),
    down: get("--down"),
  };
}

export function baseOptions(
  c: ChartColors,
  height: number,
  priceFormatter: (price: number) => string,
): DeepPartial<ChartOptions> {
  return {
    autoSize: true,
    height,
    layout: {
      background: { type: ColorType.Solid, color: c.panel },
      textColor: c.muted,
      fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
      fontSize: 12,
      attributionLogo: false,
    },
    grid: { vertLines: { color: c.rule }, horzLines: { color: c.rule } },
    rightPriceScale: { borderColor: c.rule },
    timeScale: { borderColor: c.rule, timeVisible: false },
    crosshair: { mode: CrosshairMode.Normal, vertLine: { color: c.muted }, horzLine: { color: c.muted } },
    localization: { priceFormatter },
  };
}

/** Appends an alpha channel to a 6 digit hex colour. */
export const withAlpha = (hex: string, alpha: number) =>
  `${hex}${Math.round(alpha * 255).toString(16).padStart(2, "0")}`;

/** Moving average line colours. Mid tones that read on both themes. */
export const INDICATOR_COLORS: Record<string, string> = {
  sma20: "#d9992b",
  sma50: "#a47be0",
  sma200: "#3fb3c4",
  ema20: "#e0698f",
};
