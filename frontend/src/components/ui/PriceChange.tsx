import { cn } from "../../utils/cn";
import { formatPct } from "../../utils/format";

/** Direction is shown by arrow and sign as well as colour. */
export default function PriceChange({ value, className }: { value: number | null | undefined; className?: string }) {
  if (value == null || Number.isNaN(value)) return <span className={cn("text-muted", className)}>n/a</span>;
  const up = value > 0;
  const down = value < 0;
  return (
    <span className={cn("num inline-flex items-center gap-1", up && "text-up", down && "text-down", !up && !down && "text-muted", className)}>
      <span aria-hidden="true" className="text-[0.7em]">{up ? "▲" : down ? "▼" : "■"}</span>
      <span className="sr-only">{up ? "Up" : down ? "Down" : "Unchanged"}</span>
      {formatPct(value)}
    </span>
  );
}
