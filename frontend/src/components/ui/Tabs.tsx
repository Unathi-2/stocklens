import type { KeyboardEvent } from "react";
import { cn } from "../../utils/cn";

export interface TabItem {
  id: string;
  label: string;
  disabled?: boolean;
}

interface Props {
  tabs: TabItem[];
  value: string;
  onChange: (id: string) => void;
  label: string;
}

export default function Tabs({ tabs, value, onChange, label }: Props) {
  const enabled = tabs.filter((t) => !t.disabled);

  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const i = enabled.findIndex((t) => t.id === value);
    const next = e.key === "ArrowRight" ? (i + 1) % enabled.length : (i - 1 + enabled.length) % enabled.length;
    onChange(enabled[next].id);
  };

  return (
    <div role="tablist" aria-label={label} onKeyDown={onKeyDown} className="flex gap-1 overflow-x-auto border-b border-rule">
      {tabs.map((t) => {
        const selected = t.id === value;
        return (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={selected}
            aria-disabled={t.disabled || undefined}
            tabIndex={selected ? 0 : -1}
            title={t.disabled ? "Arrives in a later phase" : undefined}
            onClick={() => !t.disabled && onChange(t.id)}
            className={cn(
              "-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              selected ? "border-accent text-ink" : "border-transparent text-muted",
              t.disabled ? "cursor-not-allowed opacity-50" : "hover:text-ink",
            )}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}
