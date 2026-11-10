import type { SelectHTMLAttributes } from "react";
import { cn } from "../../utils/cn";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: { value: string; label: string }[];
}

export default function Select({ label, options, className, id, ...rest }: Props) {
  const selectId = id ?? `select-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={selectId} className="text-sm text-muted">{label}</label>
      <select
        id={selectId}
        className={cn("rounded border border-rule bg-panel px-3 py-1.5 text-sm text-ink", className)}
        {...rest}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}
