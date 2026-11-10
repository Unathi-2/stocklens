const PATHS = {
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M14 14h7v7h-7z M3 14h7v7H3z",
  bars: "M4 20V10 M10 20V4 M16 20v-7 M22 20H2",
  star: "M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.8 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z",
  briefcase: "M3 8h18v12H3z M9 8V5h6v3",
  activity: "M3 12h4l3-8 4 16 3-8h4",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
  trend: "M3 17l6-6 4 4 8-8 M15 7h6v6",
  sliders: "M4 6h10 M18 6h2 M4 12h4 M12 12h8 M4 18h12 M14 4v4 M8 10v4 M16 16v4",
  search: "M11 4a7 7 0 100 14 7 7 0 000-14z M21 21l-5-5",
  sun: "M12 8a4 4 0 100 8 4 4 0 000-8z M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l1.5 1.5 M17.5 17.5L19 19 M5 19l1.5-1.5 M17.5 6.5L19 5",
  moon: "M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z",
  menu: "M3 6h18 M3 12h18 M3 18h18",
  close: "M6 6l12 12 M18 6L6 18",
  layers: "M12 3l9 5-9 5-9-5z M3 13l9 5 9-5",
} as const;

export type IconName = keyof typeof PATHS;

export default function Icon({ name, size = 18, className }: { name: IconName; size?: number; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
