import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

/** A row of figures separated by hairlines, like a printed ledger. */
export function Ledger({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("grid gap-px overflow-hidden rounded-md border border-rule bg-rule", className)}>
      {children}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  large?: boolean;
  loading?: boolean;
  className?: string;
}

export function MetricCard({ label, value, note, large, loading, className }: MetricCardProps) {
  return (
    <div className={cn("bg-panel px-4 py-3", className)}>
      <div className="text-sm text-muted">{label}</div>
      {loading ? (
        <div className="mt-2 h-7 w-24 animate-pulse rounded bg-panel2" />
      ) : (
        <div className={large ? "figure mt-1 text-3xl" : "num mt-1 text-lg font-medium"}>{value}</div>
      )}
      {note && <div className="mt-1 text-sm">{note}</div>}
    </div>
  );
}
