import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

type Tone = "neutral" | "up" | "down" | "accent";
const TONES: Record<Tone, string> = {
  neutral: "border-rule text-muted",
  up: "border-up text-up",
  down: "border-down text-down",
  accent: "border-accent text-accent",
};

export default function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded border px-2 py-0.5 text-xs font-medium", TONES[tone])}>
      {children}
    </span>
  );
}
