import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

interface Props {
  pressed: boolean;
  onChange: (pressed: boolean) => void;
  children: ReactNode;
  /** Optional colour swatch, used to match a chart line. */
  swatch?: string;
}

export default function Toggle({ pressed, onChange, children, swatch }: Props) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      onClick={() => onChange(!pressed)}
      className={cn(
        "inline-flex items-center gap-2 rounded border px-2.5 py-1 text-sm transition-colors",
        pressed ? "border-ink text-ink" : "border-rule text-muted hover:text-ink",
      )}
    >
      {swatch && (
        <span
          aria-hidden="true"
          className="h-2 w-2 rounded-full"
          style={{ background: pressed ? swatch : "transparent", boxShadow: `inset 0 0 0 1.5px ${swatch}` }}
        />
      )}
      {children}
    </button>
  );
}
