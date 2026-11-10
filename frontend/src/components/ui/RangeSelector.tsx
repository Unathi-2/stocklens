import { cn } from "../../utils/cn";

interface Props<V extends string> {
  options: { value: V; label: string }[];
  value: V;
  onChange: (v: V) => void;
  label: string;
}

/** Segmented control, for example 1M 3M 1Y. */
export default function RangeSelector<V extends string>({ options, value, onChange, label }: Props<V>) {
  return (
    <div role="group" aria-label={label} className="inline-flex overflow-hidden rounded border border-rule">
      {options.map((o, i) => (
        <button
          key={o.value}
          type="button"
          aria-pressed={o.value === value}
          onClick={() => onChange(o.value)}
          className={cn(
            "px-3 py-1.5 text-sm font-medium transition-colors",
            i > 0 && "border-l border-rule",
            o.value === value ? "bg-accent text-accent-fg" : "text-muted hover:bg-panel2 hover:text-ink",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
